from selenium import webdriver
from bs4 import BeautifulSoup
import requests, os, re

# Парсинг:
# https://online-samsung.ru/smartfony/
# https://online-samsung.ru/planshety/

class Samsung:
    def __init__(self):
        self.driver = webdriver.Chrome()

    def parsing(self, url):
        # открываем url
        self.driver.get(url)

        if url == 'https://online-samsung.ru/smartfony/':
            # Выбор все
            btn = self.driver.find_element_by_css_selector('#pager-filter-count-item-4')
            self.driver.execute_script("return arguments[0].click();", btn)

        # Все элементы
        els = self.driver.find_elements_by_css_selector('div[data-product-brand="SAMSUNG"]')
        # print(len(els))
        for el in els:
            link = 'https://online-samsung.ru' + el.get_attribute('about')
            print(link)
            self.parsing_one(link)

    def parsing_one(self, url):
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        article = soup.select_one('#right-col-content .even').text
        
        # Корректное ли заполнение (или поправить нужно ручками)
        spans = soup.select('#page-title span')
        if len(spans) == 2:
            model = spans[0].text
            storage, color = spans[1].text.split(',')
            storage = storage.strip()
            color = color.strip()
        else:
            model = soup.select_one('#page-title').text
            model = model[re.search(r'Samsung', model).start():]
            storage = '!!!'
            color = '!!!'
        
        line = '{};{};{};{}\n'.format(article, model, storage, color)
        print(line)
        with open('online-samsung_ru.csv', 'a', encoding='utf-8') as file:
            file.write(line)

    def __del__(self):
        self.driver.quit()
        # pass

def main():
    if os.path.exists('online-samsung_ru.csv'):
        os.remove('online-samsung_ru.csv')

    samsung = Samsung()

    urls = ['https://online-samsung.ru/smartfony/',
            'https://online-samsung.ru/planshety/']

    for url in urls:
        samsung.parsing(url)

if __name__ == '__main__':
    main()