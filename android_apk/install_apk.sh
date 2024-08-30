#!/bin/bash
#
# install apk to device
#

# manually connect to device:
# sudo adb start-server
# adb devices

sudo adb start-server

# file with apk names
file="./packages"
# folder for downloaded apk
folder="./apk"

# cmp version_phone version_download
cmp() {
    temp_phone=''
    temp_download=''
    ver_phone=`echo $1`
    ver_download=`echo $2`

    while [[ $ver_phone != $temp_phone ]]; do
        temp_phone=`echo $ver_phone | cut -d. -f1 | sed -E 's/^0+([0-9]+)/\1/g'`
        temp_download=`echo $ver_download | cut -d. -f1 | sed -E 's/^0+([0-9]+)/\1/g'`
        if (( $temp_phone > $temp_download )); then
            # echo ">>> $temp_phone > $temp_download"
            return 0
        elif (( $temp_phone < $temp_download )); then
            # echo "<<< $temp_phone < $temp_download"
            return 1
        fi
        ver_phone=`echo $ver_phone | cut -d. -f2- | sed -E 's/^0+([0-9]+)/\1/g'`
        ver_download=`echo $ver_download | cut -d. -f2- | sed -E 's/^0+([0-9]+)/\1/g'`
    done
    return 0
}

# install apk loop
IFS=$'\n'
for line in `cat $file`; do
    name=`echo "$line" | awk '{print $1}'`
    id=`echo "$line" | awk '{print $2}'`
    echo "$name"

    # ver: 3.46.0_h -> 3.46.0; 2.30.7-rc5 -> 2.30.7
    version_device=`adb shell dumpsys package $id | grep versionName | cut -d= -f2 | cut -d- -f1 | cut -d_ -f1 | tr + . `
    echo "device : $version_device"

    version_download=`ls $folder/$name* | cut -d: -f3 | sed -n 1p | tr + . `
    echo "download : $version_download"

    # cmp version_phone version_download
    cmp $version_device $version_download
    status_cmp=$?
    if (( $status_cmp == 1 )); then
        install=`ls $folder/$name*`
        echo "Need install: $install"

        # uncomment for install
        adb install-multiple -r $install
    else
        echo "Ok"
    fi

    echo "======="
done

# manually disconnect to device:
# adb kill-server

adb kill-server

