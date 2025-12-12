#!/bin/bash

#
# Получаем временные метки с заданного смещения и шага в пределах заданного времени
#

if [ $# -ne 3 ]; then
    echo "Ошибка: не указаны необходимые аргументы!"
    echo "1: Время (в минутах ИЛИ в формате М:С, например 3:35)"
    echo "2: Шаг в секундах"
    echo "3: Начальная секунда (от 0 и выше)"
    echo
    echo "Примеры вызова:"
    echo "$0 5 10 0          # 5 минут"
    echo "$0 3:35 10 5       # 3 мин 35 сек"
    exit 3
fi

time_arg=$1
step_seconds=$2
start_seconds=$3

# --- Парсим time_arg → total_seconds ---
if [[ "$time_arg" =~ ^[0-9]+$ ]]; then
    minutes_part="$time_arg"
    seconds_part=0
    total_seconds=$((minutes_part * 60))
elif [[ "$time_arg" =~ ^([0-9]+):([0-5]?[0-9])$ ]]; then
    minutes_part="${BASH_REMATCH[1]}"
    seconds_part="${BASH_REMATCH[2]}"
    total_seconds=$((minutes_part * 60 + seconds_part))
else
    echo "Ошибка: некорректный формат времени. Используйте либо число (минуты), либо М:С (например, 3:35)."
    exit 3
fi

# --- Проверка остальных аргументов ---
if ! [[ "$step_seconds" =~ ^[0-9]+$ ]] || \
   ! [[ "$start_seconds" =~ ^[0-9]+$ ]]; then
    echo "Ошибка: шаг и начальная секунда должны быть целыми неотрицательными числами."
    exit 3
fi

if [ "$step_seconds" -eq 0 ]; then
    echo "Ошибка: шаг должен быть больше нуля."
    exit 3
fi

if [ "$start_seconds" -gt "$total_seconds" ]; then
    echo "Ошибка: начальная секунда выходит за пределы заданного времени."
    exit 3
fi

# --- Генерация точек и их нумерация ---
declare -A point_to_index
index=1
for ((i = start_seconds; i <= total_seconds; i += step_seconds)); do
    point_to_index[$i]=$index
    ((index++))
done

# --- Функция вывода строки в формате MM:SS ---
print_row() {
    local secs=$1
    local min_part=$((secs / 60))
    local sec_part=$((secs % 60))
    local label
    if [[ -n "${point_to_index[$secs]}" ]]; then
        label="${point_to_index[$secs]}"
    else
        label="-"
    fi
    printf "| %02d:%02d | %s |\n" "$min_part" "$sec_part" "$label"
}

# --- Вывод: всегда первая строка — 00:00 ---
print_row 0

# --- Вывод промежуточных точек (кроме 0 и total_seconds) ---
for ((i = start_seconds; i <= total_seconds; i += step_seconds)); do
    if [ "$i" -eq 0 ] || [ "$i" -eq "$total_seconds" ]; then
        continue
    fi
    print_row "$i"
done

# --- Вывод: всегда последняя строка — конечное время (если не 0) ---
if [ "$total_seconds" -ne 0 ]; then
    print_row "$total_seconds"
fi

