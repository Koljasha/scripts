# парсинг игр Steam со скидками
# requirements.txt: beautifulsoup4, lxml, requests

import requests, os, csv
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
        except:
            continue
        sale.append({
            'title':title,
            'link': link,
            'discount': discount
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
        print(f'Page: {page}')


def write_csv(data):
    with open('steam.csv', 'a', newline='', encoding="utf-8") as file:
        fieldnames = ['title', 'link', 'discount']
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter ='|')

        for line in data:
            writer.writerow(line)


def main():
    if os.path.exists('steam.csv'):
        os.remove('steam.csv')

    with open('steam.csv', 'a', newline='', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter='|')
        writer.writerow(['Title', 'Link', 'Discount'])

    steam()


if __name__ == '__main__':
    main()

