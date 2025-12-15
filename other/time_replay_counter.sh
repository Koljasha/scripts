#!/usr/bin/env bash

# ==============================================================================
# Генератор временных меток с поддержкой дробных шагов и стартов.
# Вывод: всегда в формате MM:SS.ss (два знака после точки, даже если .00).
#
# Примеры:
#   ./time_replay_counter.sh --time=2          --step=0.5
#   ./time_replay_counter.sh --time=1:30.5     --step=10.25 --start=5.75
#   ./time_replay_counter.sh -t 5 -p 1.33 -s 0
#
# Требования:
#   - GNU getopt (из util-linux)
#   - bc (для парсинга дробных чисел)
# ==============================================================================

if ! getopt --version | grep -q "util-linux"; then
    echo "ОШИБКА: требуется GNU getopt (пакет util-linux). BSD-версия не поддерживается." >&2
    exit 1
fi

if ! command -v bc >/dev/null; then
    echo "ОШИБКА: требуется утилита 'bc' для парсинга дробных чисел." >&2
    exit 1
fi

# Парсим аргументы
PARSED=$(getopt -o t:p:s: -l time:,step:,start: -n "$0" -- "$@")
if [[ $? -ne 0 ]]; then
    echo "ОШИБКА: сбой при разборе аргументов." >&2
    exit 2
fi
eval set -- "$PARSED"

time_arg=""
step_arg=""
start_arg=""

while true; do
    case $1 in
        -t|--time)   time_arg="$2";   shift 2 ;;
        -p|--step)   step_arg="$2";   shift 2 ;;
        -s|--start)  start_arg="$2";  shift 2 ;;
        --) shift; break ;;
        *) echo "ВНУТРЕННЯЯ ОШИБКА"; exit 3 ;;
    esac
done

# Проверка обязательных параметров
if [[ -z "$time_arg" || -z "$step_arg" ]]; then
    cat >&2 <<EOF
ОШИБКА: обязательные параметры --time (-t) и --step (-p) не заданы.

Использование:
  $0 --time=<время> --step=<шаг> [--start=<старт>]
  $0 -t <время> -p <шаг> [-s <старт>]

Форматы времени:
  - Минуты:          "5"        → 5 минут
  - Мин:Сек:         "1:30"     → 1 минута 30 секунд
  - Мин:Сек.сс:      "1:30.25"  → 1:30 и 25 сотых секунды

Примеры:
  $0 -t 2 -p 0.5
  $0 --time=1:45.5 --step=10.25 --start=5.75
EOF
    exit 3
fi

# Устанавливаем start = step, если не задан
if [[ -z "$start_arg" ]]; then
    start_arg="$step_arg"
fi

# ==============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================

# Преобразует строку времени в целое число — сотые доли секунды
parse_time_to_centiseconds() {
    local input="$1"
    local total_sec

    if [[ "$input" =~ ^[0-9]+$ ]]; then
        total_sec=$(echo "$input * 60" | bc -l)
    elif [[ "$input" =~ ^([0-9]+):([0-5]?[0-9])(\.[0-9]+)?$ ]]; then
        local min="${BASH_REMATCH[1]}"
        local sec="${BASH_REMATCH[2]}"
        local frac="${BASH_REMATCH[3]:-.0}"
        total_sec=$(echo "$min * 60 + $sec$frac" | bc -l)
    else
        echo "ОШИБКА: неверный формат времени '$input'. Ожидалось: Ч или Ч:С или Ч:С.дд" >&2
        exit 3
    fi

    # Округляем до ближайшей сотой и возвращаем целое (без точки!)
    local cs=$(echo "scale=0; ($total_sec * 100 + 0.5)/1" | bc -l)
    echo "${cs%.*}"
}

# Преобразует целое число сотых секунд → строка MM:SS.ss
centiseconds_to_mmss() {
    local cs="$1"
    # Убедимся, что это число
    if ! [[ "$cs" =~ ^[0-9]+$ ]]; then
        echo "ОШИБКА: centiseconds_to_mmss получил не число: '$cs'" >&2
        exit 3
    fi

    local total_sec=$((cs / 100))
    local frac_part=$((cs % 100))
    local minutes=$((total_sec / 60))
    local seconds=$((total_sec % 60))

    printf "%02d:%02d.%02d" "$minutes" "$seconds" "$frac_part"
}

# Проверка: неотрицательное число (для step/start)
is_nonnegative_number() {
    [[ "$1" =~ ^[0-9]*\.?[0-9]+$ ]] || [[ "$1" =~ ^[0-9]+$ ]]
}

# ==============================================================================
# ПРЕОБРАЗОВАНИЕ ВХОДНЫХ ДАННЫХ В ЦЕЛЫЕ СОТЫЕ ДОЛИ СЕКУНД
# ==============================================================================

# Проверяем корректность step и start как чисел
if ! is_nonnegative_number "$step_arg" || ! is_nonnegative_number "$start_arg"; then
    echo "ОШИБКА: шаг (--step/-p) и старт (--start/-s) должны быть неотрицательными числами." >&2
    exit 3
fi

# Конвертируем всё в целые сотые доли секунды (гарантированно целые строки)
total_cs_str=$(parse_time_to_centiseconds "$time_arg")
step_cs_str=$(echo "scale=0; ($step_arg * 100 + 0.5)/1" | bc -l)
start_cs_str=$(echo "scale=0; ($start_arg * 100 + 0.5)/1" | bc -l)

# Убираем возможную дробную часть (защита от 12200.0)
total_cs="${total_cs_str%.*}"
step_cs="${step_cs_str%.*}"
start_cs="${start_cs_str%.*}"

# Проверяем, что получили только цифры
if ! [[ "$total_cs" =~ ^[0-9]+$ ]] || ! [[ "$step_cs" =~ ^[0-9]+$ ]] || ! [[ "$start_cs" =~ ^[0-9]+$ ]]; then
    echo "ОШИБКА: не удалось преобразовать параметры в целые числа." >&2
    exit 3
fi

# Преобразуем в числа для арифметики
total_cs=$((total_cs))
step_cs=$((step_cs))
start_cs=$((start_cs))

# Финальные проверки
if (( step_cs <= 0 )); then
    echo "ОШИБКА: шаг должен быть больше нуля." >&2
    exit 3
fi

if (( start_cs > total_cs )); then
    echo "ОШИБКА: начальная точка выходит за пределы заданного времени." >&2
    exit 3
fi

# ==============================================================================
# ГЕНЕРАЦИЯ ТОЧЕК
# ==============================================================================

declare -A point_to_index
index=1

current=$start_cs
while (( current <= total_cs )); do
    point_to_index[$current]=$index
    ((index++))
    ((current += step_cs))
done

# ==============================================================================
# СБОРКА И ВЫВОД
# ==============================================================================

# Список точек: 0, промежуточные (без 0 и total), total (если ≠ 0)
output_points=(0)

for pt in "${!point_to_index[@]}"; do
    if (( pt == 0 || pt == total_cs )); then
        continue
    fi
    output_points+=($pt)
done

if (( total_cs > 0 )); then
    output_points+=($total_cs)
fi

# Сортируем
IFS=$'\n' sorted_points=($(sort -n <<<"${output_points[*]}"))
unset IFS

# Вывод сводки параметров
printf "=====================\n"
printf "Время: %s  Шаг: %s  Старт: %s\n" \
    "$(centiseconds_to_mmss "$total_cs")" \
    "$(centiseconds_to_mmss "$step_cs")" \
    "$(centiseconds_to_mmss "$start_cs")"
printf "=====================\n"

# Вывод
for pt in "${sorted_points[@]}"; do
    mmss=$(centiseconds_to_mmss "$pt")
    label="${point_to_index[$pt]:--}"
    printf "| %s | %s |\n" "$mmss" "$label"
done
printf "=====================\n"


