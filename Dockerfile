FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Устанавливаем системные зависимости (certs, curl) и обновляем pip
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip

# Ставим Python зависимости
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Копируем остальной код
COPY . .

EXPOSE 5000

# Запуск через gunicorn
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "120"]