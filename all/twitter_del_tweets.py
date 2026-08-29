#!/usr/bin/env python

#
# Delete tweets from account
# need config.py with Twitter keys and tokens
#
# pip install requests requests_oauthlib
#

import requests
from requests_oauthlib import OAuth1

from config import consumer_key_TW, consumer_secret_TW, access_token_TW, access_token_secret_TW

def main():

    auth = OAuth1(consumer_key_TW, consumer_secret_TW, access_token_TW, access_token_secret_TW)

    url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
    params = {
        "screen_name": "Koljasha",
        "count": 25
    }
    res = requests.get(url, params=params, auth=auth).json()


    for_del = []
    for count, i in enumerate(res):
        print(count, ' : ', i['id_str'])
        print(i['text'])
        print('=====')
        for_del.append(i['id_str'])

    print('=========================')

    not_del = ['1353734459456172036']

    for i in for_del:
        if i not in not_del:
            print(f'Will be delete: {i}')

            # uncomment next two lines to delete tweets
            # url = f'https://api.twitter.com/1.1/statuses/destroy/{i}.json'
            # res = requests.post(url, auth=auth).json()

if __name__ == '__main__':
    main()

