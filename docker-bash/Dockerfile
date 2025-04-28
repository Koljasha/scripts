# Используем Ubuntu как базовый образ
FROM ubuntu:latest

# Устанавливаем необходимые пакеты и настраиваем временную зону и Cron
# вывод Cron в stdout
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata coreutils cron && \
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "* * * * * root /app/script.sh >> /proc/1/fd/1 2>> /proc/1/fd/2" > /etc/cron.d/usercron && \
    chmod 0644 /etc/cron.d/usercron

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем скрипт в рабочую директорию
COPY script.sh .

# Запускаем cron в режиме foreground, чтобы контейнер не завершался
CMD ["cron", "-f"]

