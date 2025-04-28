# Используем Ubuntu как базовый образ
FROM ubuntu:latest

# Устанавливаем пакеты tzdata, coreutils и cron
RUN apt-get update && \
    apt-get install -y tzdata coreutils cron && \
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем скрипт в рабочую директорию
COPY script.sh .

# Настраиваем cron
RUN echo "* * * * * /app/script.sh" > /etc/cron.d/usercron && \
chmod 0644 /etc/cron.d/usercron && \
crontab /etc/cron.d/usercron

# Запускаем cron в foreground
CMD ["cron", "-f"]

