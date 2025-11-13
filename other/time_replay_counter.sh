#!/bin/bash

#
# Получаем количество повторов за X минут
#

if ! [[ $# =~ [3] ]]; then
    echo "There are no necessary arguments!"
    echo "1: Количество минут"
    echo "2: Шаг в секундах"
    echo "3: Начало 00:00 учитываем (0|1)"

    echo "Example of a call:"
    echo "$0 2 5 0"

    exit 3
fi

total_minutes=$1
step_seconds=$2
zero_time=$3

# Общее количество секунд
total_seconds=$((total_minutes * 60))

# Генерация временных меток
index=$zero_time
for ((i=0; i<=total_seconds; i+=step_seconds)); do
    min_part=$((i / 60))  # Получаем минуты
    sec_part=$((i % 60))   # Получаем секунды
    printf "| %d мин %d сек | %d |\n" "$min_part" "$sec_part" "$index"
    index=$((index + 1))
done

