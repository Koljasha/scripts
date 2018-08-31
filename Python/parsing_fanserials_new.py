# парсинг новинок сайта http://fanserials.cc/new/ с записью в csv
# requirements.txt: beautifulsoup4, lxml, requests

import requests, csv
from bs4 import BeautifulSoup


def get_html(url):
    return requests.get(url).text


def paginator(url):
    soup = BeautifulSoup(get_html(url), "lxml")
    last = soup.find('ul', {'class':'pagination'}).find_all('li')[-2].find('a').text.strip()
    return int(last)


def write_csv(data):
    with open('fanserials.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow( (data['name'],
                          data['seria'],
                          data['translate'],
                          data['url']) )


def get_page_data(url):
    soup = BeautifulSoup(get_html(url), "lxml")
    films = soup.find('ul', id='serias-list').find_all('li')

    for film in films:
        # имя сериала, серия
        name = film.find('div', class_='field-title').find('a').text.strip()
        seria = film.find('div', class_='field-description').find('a').text.strip()

        # перевод
        translates = film.find('div', class_='first-line').find_all('a')
        for translate in translates:
            data = {'name':name,
                    'seria':seria,
                    'translate':translate.text.strip(),
                    'url':translate.get('href')}
            write_csv(data)


def main():
    # есть paginator(url) - для определения последней страницы (return int)
    last = input("Последняя страница: ").strip()
    for i in range(1, int(last)+1):
        url = 'http://fanserials.cc/new/page/' + str(i) + '/'
        get_page_data(url)
        print(".", end='')


if __name__ == "__main__":
    main()

