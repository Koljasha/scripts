# Используем официальный образ Python как базовый
FROM python:slim

# Устанавливаем пакеты
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata cron procps && \
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Создаем Cron
COPY cronfile /etc/cron.d/

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Установка Django
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем entrypoint
COPY entrypoint.sh /entrypoint.sh

# Копируем проект и script.sh
COPY app/ .

# Порт для Django
EXPOSE 8000

# Устанавливаем entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Команда запуска сервера Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

