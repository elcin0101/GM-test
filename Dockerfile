# Используем Python 3.12 + совместимый Playwright
FROM mcr.microsoft.com/playwright/python:v1.50.0-jammy

# Устанавливаем зависимости
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Устанавливаем браузеры
RUN playwright install --with-deps

# Копируем код
COPY . .

# Запуск приложения
CMD ["python", "test_start.py"]  