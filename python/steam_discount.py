#!/usr/bin/env python

#
# парсинг игр Steam со скидками
#
# pip install requests beautifulsoup4 lxml
#

import requests, os, csv, webbrowser, argparse
from bs4 import BeautifulSoup


def get_html(url, params):
    data = requests.get(url, params=params)
    if data.status_code != 200:
        raise Exception('Error status code')
    return data.text


def paginator(url, params):
    data = get_html(url, params)
    bs = BeautifulSoup(data, 'lxml')
    pags = bs.select('.search_pagination_right > a')
    return pags[-2].text.strip()


def discount(url, params):
    data = get_html(url, params)
    bs = BeautifulSoup(data, 'lxml')
    games = bs.select('.responsive_search_name_combined')

    sale = []

    for game in games:
        title = game.select('.title')[0].text.strip()
        link = game.parent.get('href').split('?')[0]
        try:
            discount = game.select('.search_discount > span')[0].text.strip()
        except Exception:
            continue
        price = game.select('.search_price')[0].text.strip().split('.')
        sale.append({
            'title': title,
            'link': link,
            'discount': discount,
            'full_price': price[0],
            'discount_price': price[1]
        })

    return sale


def steam():
    url = 'https://store.steampowered.com/search/'

    # specials = 1 - не показывает скидки 100%
    # в итоге парсим весь магазин
    params = {
        # 'specials': 1,
        'ignore_preferences': 1,
        'count': 100,
    }

    try:
        params['page'] = 1
        pag = int(paginator(url, params))
    except Exception as e:
        print(f'Exception: {e}')
        return

    print('Paginator:', pag)

    for page in range(1, pag + 1):
        params['page'] = page
        try:
            discounts = discount(url, params)
        except Exception as e:
            print(f'Exception: {e}')
            return

        write_csv(discounts)
        print(f'Page: {page} / {pag}')


def write_csv(data):
    with open('steam.csv', 'a', newline='', encoding='utf-8') as file:
        fieldnames = ['title', 'link', 'discount', 'full_price', 'discount_price']
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='|')

        for line in data:
            writer.writerow(line)

def read_csv(browser=False):
    try:
        with open('steam.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='|')
            for row in reader:
                if row['Discount'] == '-100%':
                    if browser:
                        webbrowser.open_new_tab(row['Link'])
                    else:
                        print(row['Title'], '\t|\t', row['Link'])
    except Exception as e:
        print(f'Exception: {e}')
        return


def main():
    parser = argparse.ArgumentParser(description='Parse Steam Store for discount', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-p', '--parse', action='store_true', help='Parse Steam Store and write steam.csv')
    parser.add_argument('-s', '--show', default=0, type=int, choices=range(3), help='0 - Not show anything;\n1 - Show games with 100 discount in script;\n2 - Show games with 100 discount in browser from steam.csv')
    args = parser.parse_args()

    if args.parse is False and args.show ==  0:
        parser.print_help()
        return

    if args.parse is True:
        if os.path.exists('steam.csv'):
            os.remove('steam.csv')

        with open('steam.csv', 'a', newline='', encoding="utf-8") as file:
            writer = csv.writer(file, delimiter='|')
            writer.writerow(['Title', 'Link', 'Discount', 'Full price', 'Discount price'])

        steam()

        print('---------------')
        if args.show == 2:
            read_csv(True)
        elif args.show == 1:
            read_csv(False)
        print('---------------')

    else:
        if args.show == 2:
            read_csv(True)
        elif args.show == 1:
            read_csv(False)

if __name__ == '__main__':
    main()

