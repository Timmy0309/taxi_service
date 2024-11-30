from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
import psycopg2 # type: ignore
from psycopg2.extras import RealDictCursor # type: ignore
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host="database",
            database="taxi_service",
            user="user",
            password="pass"
        )
        return connection
    except psycopg2.OperationalError as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise


def generate_unique_order_number():
    """Генерирует уникальный пятизначный номер заказа."""
    connection = get_db_connection()
    cursor = connection.cursor()
    while True:
        order_number = f"{random.randint(10000, 99999)}"
        cursor.execute("SELECT 1 FROM orders WHERE order_number = %s;", (order_number,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return order_number


@app.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        if not data or 'pickup' not in data or 'destination' not in data:
            return jsonify({'error': 'Invalid data: pickup and destination are required'}), 400

        order_number = generate_unique_order_number()

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO orders (pickup, destination, status, order_number) VALUES (%s, %s, %s, %s) RETURNING id;",
            (data['pickup'], data['destination'], 'new', order_number)
        )
        order_id = cursor.fetchone()[0]
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'order_id': order_id, 'order_number': order_number}), 201
    except psycopg2.Error as e:
        logger.error(f"Ошибка базы данных: {e}")
        return jsonify({'error': 'Failed to create order'}), 500
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/orders/number/<order_number>', methods=['GET'])
def get_order_by_number(order_number):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT o.id, o.pickup, o.destination, o.status, o.order_number, d.name AS driver_name
            FROM orders o
            LEFT JOIN drivers d ON o.driver_id = d.id
            WHERE o.order_number = %s;
        """, (order_number,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Order not found'}), 404
    except psycopg2.Error as e:
        logger.error(f"Ошибка базы данных: {e}")
        return jsonify({'error': 'Failed to retrieve order details'}), 500
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
