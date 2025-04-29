# Используем Debian как базовый образ
FROM debian:stable-slim

# Устанавливаем необходимые пакеты
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y cron tzdata && \
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Создаем Cron
COPY cronfile /etc/cron.d/
# Даем правильные права на cronfile
# RUN chmod 0644 /etc/cron.d/cronfile

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем скрипт в рабочую директорию
COPY script.sh .

# Запускаем cron в режиме foreground, чтобы контейнер не завершался
CMD ["cron", "-f"]

