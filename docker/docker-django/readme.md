### Тестовый пример Docker: Django

* запуск: `docker compose up -d`
* пересборка: `docker compose up -d --build`

* локальный запуск:
    * `python app/manage.py runserver`
    * `gunicorn root.wsgi:application --chdir=./app --reload`

