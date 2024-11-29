# Используем официальный Python образ в качестве базового
FROM python:3.9-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем локальные файлы в контейнер
COPY requirements.txt /app/

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы (включая processor.py) в контейнер
COPY . /app/

# Запускаем процессор заказов
CMD ["python", "processor.py"]
