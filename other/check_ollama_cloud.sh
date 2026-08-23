#!/usr/bin/env bash
#
# Проверка всех моделей ollama-cloud в opencode.
# Каждой модели отправляется тестовый запрос; в конце выводится таблица:
# кто ответил, а кому нужен upgrade / более высокий тариф.
# Ключевая фишка: после каждого запроса сессия сразу удаляется из базы,
# чтобы не накапливалось мусора от тестов.

set -euo pipefail

PROMPT="Привет, что ты за модель"
CONCURRENCY=5      # параллельных проверок
TIMEOUT=120        # сек на одну модель
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

# ---------- 1. Получаем список моделей ----------
mapfile -t MODELS < <(opencode models 2>/dev/null | grep '^ollama-cloud/' || true)

if [[ ${#MODELS[@]} -eq 0 ]]; then
    echo "Модели ollama-cloud не найдены (проверь 'opencode models')" >&2
    exit 1
fi

TOTAL=${#MODELS[@]}
echo "Найдено моделей ollama-cloud: $TOTAL"
echo

# ---------- 2. Классификация ошибок ----------
classify_error() {
    local msg="$1" lower
    lower=$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')

    # Высший тариф: "requires both a Pro, Max, or Team plan and extra usage"
    # (проверяется ПЕРВЫМ, т.к. это сообщение тоже содержит "upgrade for access")
    if [[ "$lower" == *'pro, max, or team'* || "$lower" == *'extra usage'* || "$lower" == *'plan max'* || "$lower" == *'max plan'* ]]; then
        STATUS="Нужен тариф Pro/Max/Team"
    elif [[ "$lower" == *'requires a subscription'* ]]; then
        STATUS="Нужен upgrade (подписка)"
    elif [[ "$lower" == *'upgrade'* ]]; then
        STATUS="Нужен upgrade"
    elif [[ "$lower" == *'retired'* ]]; then
        STATUS="Удалена (retired)"
    elif [[ "$lower" == *'rate limit'* || "$lower" == *'too many requests'* || "$lower" == *'"code":429'* || "$lower" == *'statuscode":429'* ]]; then
        STATUS="Rate limit"
    elif [[ "$lower" == *'unauthorized'* || "$lower" == *'api key'* || "$lower" == *'auth'* ]]; then
        STATUS="Ошибка авторизации"
    elif [[ "$lower" == *'not found'* ]]; then
        STATUS="Модель не найдена"
    else
        STATUS="Другая ошибка"
    fi
}

# Сокращение длинного текста до одной строки заданной ширины
shorten() {
    local text="$1" width=$2
    text=$(printf '%s' "$text" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g; s/^ //; s/ $//')
    if (( ${#text} > width )); then
        printf '%s…' "${text:0:width-1}"
    else
        printf '%s' "$text"
    fi
}

# ---------- 3. Проверка одной модели ----------
#После каждого opencode run извлекает sessionID и сразу удаляет сессию из базы.
check_model() {
    local model="$1" idx=$2
    local safe out rc=0 detail="" status
    local session_id=""

    safe=$(printf '%s' "$model" | tr -c 'a-zA-Z0-9._-' '_')
    out="$WORKDIR/$safe.out"

    # Запуск с сохранением вывода и извлечением sessionID
    # Используем формат json, чтобы могли прочитать sessionID
    timeout "$TIMEOUT" opencode run -m "$model" --format json "$PROMPT" >"$out" 2>/dev/null || rc=$?

    # Извлекаем sessionID из JSON-output (первое встречающееся значение)
    if [[ -f "$out" && $rc -eq 0 ]]; then
        session_id=$(jq -r 'select(.sessionID != null) | .sessionID // empty' "$out" 2>/dev/null | head -n1)
    fi

    # Удаляем созданную сессию из базы RIGHT AWAY, чтобы не накапливалось мусора.
    if [[ -n "$session_id" ]] ; then
        opencode session delete $session_id > /dev/null 2>&1
    fi

    if (( rc == 0 )) && grep -q '"type":"text"' "$out"; then
        # Успех: склеиваем все текстовые части ответа
        detail=$(jq -r 'select(.type=="text") | .part.text' "$out" 2>/dev/null | paste -sd ' ')
        status="OK"
    else
        # Ошибка: достаём сообщение из события error (или из stderr-кода таймаута)
        local err=""
        err=$(jq -r 'select(.type=="error") | .error.data.message // .error.message // .message // empty' "$out" 2>/dev/null | head -n1)
        [[ -z "$err" && $rc -eq 124 ]] && err="Превышен таймаут ${TIMEOUT}s"
        [[ -z "$err" ]] && err="(exit code $rc)"
        classify_error "$err"
        status=$STATUS
        # для «сырых» ошибок показываем текст, для upgrade — краткую суть
        if [[ "$status" != "Нужен upgrade (подписка)" && "$status" != "Нужен upgrade" ]]; then
            detail=$(shorten "$err" 60)
        fi
    fi

    # Результат: idx<TAB>status<TAB>detail
    printf '%d\t%s\t%s\n' "$idx" "$status" "${detail:-}" >"$WORKDIR/$safe.result"

    printf '[%2d/%d] %-40s %s\n' "$idx" "$TOTAL" "$model" "$status" >&2
}

# ---------- 4. Запуск с ограничением параллелизма ----------
i=0
for model in "${MODELS[@]}"; do
    i=$((i + 1))
    check_model "$model" "$i" &
    # держим не более $CONCURRENCY фоновых задач
    while (( $(jobs -rp | wc -l) >= CONCURRENCY )); do
        sleep 0.3
    done
done
wait

# ---------- 5. Итоговая таблица ----------
echo
echo "==================== РЕЗУЛЬТАТЫ ===================="
printf '%-4s %-36s %-26s %s\n' '#' 'МОДЕЛЬ' 'СТАТУС' 'ОТВЕТ / ДЕТАЛИ'
printf '%s\n' "$(printf '%.0s-' {1..130})"

ok_count=0
fail_count=0
i=0
for model in "${MODELS[@]}"; do
    i=$((i + 1))
    safe=$(printf '%s' "$model" | tr -c 'a-zA-Z0-9._-' '_')
    IFS=$'\t' read -r _idx status detail <"$WORKDIR/$safe.result"

    if [[ "$status" == "OK" ]]; then
        ok_count=$((ok_count + 1))
        color='\033[32m'
    else
        fail_count=$((fail_count + 1))
        color='\033[31m'
    fi
    reset='\033[0m'

    printf '%-4d %-36s %b%-26s%b %s\n' "$i" "$model" "$color" "$(shorten "$status" 26)" "$reset" "$(shorten "$detail" 55)"
done

printf '%s\n' "$(printf '%.0s-' {1..130})"
echo "Итого: $ok_count ответили, $fail_count с ошибкой (из $TOTAL)"
