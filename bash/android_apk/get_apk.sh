#!/bin/bash
#
# get apk from device
#

# manually connect to device:
# sudo adb start-server
# adb connect 192.168.1.127
# adb devices

sudo adb start-server

# file with apk names
file="./packages"
# folder for downloaded apk
folder="./apk"

if [[ ! -d $folder ]]; then
    mkdir $folder
else
    rm -rf $folder
    mkdir $folder
fi

# pull apk loop
IFS=$'\n'
for line in `cat $file`; do
    name=`echo "$line" | awk '{print $1}'`
    id=`echo "$line" | awk '{print $2}'`

    # ver: 3.46.0_h -> 3.46.0; 2.30.7-rc5 -> 2.30.7
    version=`adb shell dumpsys package $id | grep versionName | cut -d= -f2 | cut -d- -f1 | cut -d_ -f1`

    full_path=`adb shell pm path $id | cut -d: -f2`

    for split in `echo "$full_path" | cat -n`; do
        path=`echo "$split" | awk '{print $2}'`
        num=`echo "$split" | awk '{print $1}'`

        download=`echo "${folder}/${name}:${num}:${version}:.apk"`
        adb pull $path $download
    done
done

# manually disconnect to device:
# adb kill-server

adb kill-server

