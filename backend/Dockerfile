FROM python:3.9
WORKDIR /app
COPY ./app.py /app/app.py
RUN pip install flask psycopg2 flask_cors
EXPOSE 5000
CMD ["python", "app.py"]

