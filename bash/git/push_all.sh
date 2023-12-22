#!/usr/bin/env bash

#
# git push every folder
#

if (( $# != 1 )); then
    upstream='origin'
else
    upstream=$1
fi

for i in *; do
    if [[ ! -d $i ]]; then
        continue
    fi
    echo "*** $i ***"
    cd $i

    upstream_links=`git remote -v | grep "^$upstream"`
    if [[ "$upstream_links" == '' ]]; then
        echo "No upstream: $upstream"
    else
        git push $upstream master
    fi

    echo "---"
    cd ../
done

# bitbucket count js:
# document.querySelectorAll('.assistive + table > tbody > tr')

