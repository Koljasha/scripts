#!/usr/bin/env python

#
# парсинг Портала (ссылки изменены)
#
# pip install requests beautifulsoup4 lxml
#

import requests, csv
from bs4 import BeautifulSoup


def parce_portal(start, stop):
    data = {}

    session = requests.Session()
    session.auth = ('username', 'password')

    for i in range(start, stop+1):
        url = 'http://portal/?ID={}'.format(i)
        res = session.get(url)
        if res.status_code != 200:
            print("Error! Code {} != 200".format(res.status_code))
        soup = BeautifulSoup(res.text, 'lxml')
        try:
            product = soup.find(id='SPFieldText').text.strip()
        except AttributeError:
            product = "Ошибка - Нет Продукта"
        data[i] = product
        print(i, product)

    return data


def write_csv(data):
    with open('portal.csv', 'w', newline='', encoding='cp1251') as csvfile:
        fieldnames = ['id', 'name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

        writer.writeheader()
        for id, name in data.items():
            writer.writerow({'id': id, 'name': name})


def main():
    portal = parce_portal(1, 125)
    write_csv(portal)


if __name__ == '__main__':
    main()

