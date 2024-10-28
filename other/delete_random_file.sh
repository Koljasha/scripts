#!/usr/bin/env bash

#
# Удаляем случайные файлы в каталоге
#

# каталог откуда удаляем
folder='Wallpapers'
# количество файлов, когда перестаем удалять
stop_count=500

count=1
while : ; do
    count=`ls "$folder/" | wc -l`
    if (( $count <= $stop_count )); then
        break
    fi

    file=`ls "$folder/" | sort -R | tail -1`
    rm -v "$folder/$file"
done

echo "OK"

