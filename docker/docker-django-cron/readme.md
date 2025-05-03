### Тестовый пример Docker: Django и Cron

##### Cron в примере делает reload Gunicorn каждую минуту

* запуск: `docker compose up`
* пересборка: `docker compose up --build`

* локальный запуск:
    * `python app/manage.py runserver`
    * `gunicorn root.wsgi:application --chdir=./app --reload`

