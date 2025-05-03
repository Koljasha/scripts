#!/usr/bin/env bash

# Запускаем Cron
service cron start

# Выполняем переданную команду (или скрипт)
exec "$@"

