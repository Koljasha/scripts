#!/usr/bin/env bash

#
# печатаем дату в файл лога
#

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
SCRIPTNAME=$(basename "$0")

logs_dir="$SCRIPTPATH/logs"
if [[ ! -d $logs_dir ]]; then
    mkdir -p $logs_dir
fi
log_file="${logs_dir}/${SCRIPTNAME}.log"

date '+%Y-%m-%d %H:%M:%S' >> $log_file

