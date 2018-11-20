from bs4 import BeautifulSoup
import requests, csv, os

# Парсинг https://galaxystore.ru/

def write_csv(text, id):
    with open('galaxystore_ru.csv', 'a', newline='' , encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow( (text, id) )


def parsing(url):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    els = soup.find_all('figure')
    for el in els:
        a = el.find('a')
        id_ = a.get('href').split('/')[2]
        text = a.find('span').text
        write_csv(text, id_)


def main():
    if os.path.exists('galaxystore_ru.csv'):
        os.remove('galaxystore_ru.csv')

    urls =  ['https://galaxystore.ru/catalog/mobile/smartphone/?page_size=all',
            'https://galaxystore.ru/catalog/mobile/pocket/?page_size=all']
    for url in urls:
        parsing(url)


if __name__ == '__main__':
    main()