# Используем официальный образ Python как базовый
FROM python:slim

# Устанавливаем пакеты
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y cron tzdata && \
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Создаем Cron
COPY cronfile /etc/cron.d/cronfile
# Даем правильные права на cronfile
# RUN chmod 0644 /etc/cron.d/cronfile

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем Python-скрипт в рабочую директорию
COPY main.py .

# Запускаем cron в режиме foreground, чтобы контейнер не завершался
CMD ["cron", "-f"]

