#!/bin/bash

# Переименование файлов, выгруженных из Lightroom Mobile
# дата выгрузки -> дата фото

arr=(`ls LRM_*.jpeg`)

for line in ${arr[*]} ; do
    dt=`identify -format "%[EXIF:DateTime]\n" $line | sed 's/://g' | sed 's/\ /_/'`
    name="IMG_$dt.jpeg"
    mv $line $name
    echo "$line  -->  $name"
done

