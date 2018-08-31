# парсинг новинок сайта http://fantasy-worlds.org/lib/ с записью в csv
# requirements.txt: beautifulsoup4, lxml, requests

import requests, csv
from bs4 import BeautifulSoup


def get_html(url):
    return requests.get(url).text


def paginator(url):
    soup = BeautifulSoup(get_html(url), "lxml")
    last = soup.find('div', {'class':'pagination'}).find_all('li')[-2].find('a').find('span').next_sibling
    return int(last)


def write_csv(data):
    with open('fantasy.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow( (data['autor'],
                          data['autor_link'],
                          data['book'],
                          data['book_link'],
                          data['book_access'],
                          data['book_read'],
                          data['book_download'],
                          ) )


def get_page_data(url):
    soup = BeautifulSoup( get_html(url), "lxml" )

    books_title = soup.find('div', id='libr').find_all(class_='news_title')
    books_body = soup.find('div', id='libr').find_all(class_='news_body')
    length = len(books_title)
    for i in range(length):
        book_title = books_title[i].find('a')
        title_autor = book_title.text.split('—')[0].strip()
        title_book = book_title.text.split('—')[1].strip()
        title_link = 'http://fantasy-worlds.org' + book_title.get('href')   # http://fantasy-worlds.org/lib/id27194/

        book_body = books_body[i].find('span')
        body_autor = book_body.find('p').find('a').text.strip()
        autor_link = 'http://fantasy-worlds.org' + book_body.find('p').find('a').get('href')

        try:
            book_body.find('a', class_='_nb-normal-button').get('href')
            download = title_link + 'download/'
            read = title_link + 'read/'
            access = ''
        except:
            download = title_link + 'download/'
            read = title_link + 'read/'
            access = 'Ограничен'

        data = {'autor':body_autor,
                'autor_link':autor_link,
                'book':title_book,
                'book_link':title_link,
                'book_access':access,
                'book_read':read,
                'book_download':download}

        write_csv(data)


def main():
    # есть paginator(url) - для определения последней страницы (return int)
    first, last = input("Через пробел первую и последнюю страницы: ").strip().split(' ')
    for i in range(int(first), int(last)+1):
        url = 'http://fantasy-worlds.org/lib/' + str(i)
        get_page_data(url)
        print(".",end='')


if __name__ == '__main__':
    main()

