#!/bin/bash

#
# Получаем количество повторов за X минут
#

if ! [[ $# =~ [2] ]]; then
    echo "There are no necessary arguments!"
    echo "1: Количество минут"
    echo "2: Шаг в секундах"

    echo "Example of a call:"
    echo "$0 2 5"

    exit 3
fi

total_minutes=$1
step_seconds=$2

# Общее количество секунд
total_seconds=$((total_minutes * 60))

# Генерация временных меток
index=1
for ((i=0; i<=total_seconds; i+=step_seconds)); do
    min_part=$((i / 60))  # Получаем минуты
    sec_part=$((i % 60))   # Получаем секунды
    printf "%d | %d мин %d сек\n" "$index" "$min_part" "$sec_part"
    index=$((index + 1))
done

