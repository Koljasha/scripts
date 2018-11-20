from selenium import webdriver
from time import sleep
import os

# Парсинг:
# https://www.samsung.com/ru/smartphones/all-smartphones/
# https://www.samsung.com/ru/tablets/all-tablets/

class Samsung:
    def __init__(self):
        self.driver = webdriver.Chrome()

    def parsing(self, url):
        # открываем url
        self.driver.get(url)

        # Обрабатываем "Показать еще"
        while self.driver.find_element_by_css_selector('.btn-view-more').get_attribute('style') == "":
            btn = self.driver.find_element_by_css_selector('.btn-view-more a')
            self.driver.execute_script("return arguments[0].click();", btn)
            sleep(1)

        # Всего моделей
        length_elem = len(self.driver.find_elements_by_css_selector('.type-A'))
        # print('Length:', length_elem)

        with open('samsung_com.csv', 'a', encoding='utf-8') as file:

            for i in range(length_elem):
                # Цветов у модели
                els = self.driver.find_elements_by_css_selector('.type-A')
                length_colors = len(els[i].find_elements_by_css_selector('ul.s-slick .product-card__img-ctrl-item a'))
                # print('Color:', length_colors)

                for j in range(length_colors):
                    btn_color = els[i].find_elements_by_css_selector('ul.s-slick .product-card__img-ctrl-item a')[j]
                    self.driver.execute_script("return arguments[0].click();", btn_color)

                    els = self.driver.find_elements_by_css_selector('.type-A')
                    model = els[i].find_element_by_css_selector('.product-card__prd-info-title-wrap span').text
                    model_id, id = els[i].get_attribute('data-omni').split('|')
                    color = els[i].find_elements_by_css_selector('ul.s-slick .product-card__img-ctrl-item span')[j].get_attribute('innerHTML')

                    if color == 'blue':
                        color = 'синий'
                    elif color == 'dukeblue':
                        color = 'синий'
                    elif color == 'black':
                        color = 'черный'
                    elif color == 'BLACK':
                        color = 'черный'
                    elif color == 'silver':
                        color = 'серебристый'
                    elif color == 'gold':
                        color = 'золотой'
                    elif color == 'white':
                        color = 'белый'

                    line = '{};{};{};{}\n'.format(model, model_id, id, color)
                    print(line)
                    file.write(line)


    def __del__(self):
        self.driver.quit()


def main():
    if os.path.exists('samsung_com.csv'):
        os.remove('samsung_com.csv')

    urls = [ 'https://www.samsung.com/ru/smartphones/all-smartphones/',
            'https://www.samsung.com/ru/tablets/all-tablets/' ]

    samsung = Samsung()
    
    for url in urls:
        samsung.parsing(url)


if __name__ == '__main__':
    main()