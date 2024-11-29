from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

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

@app.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        if not data or 'pickup' not in data or 'destination' not in data:
            return jsonify({'error': 'Invalid data: pickup and destination are required'}), 400

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO orders (pickup, destination, status) VALUES (%s, %s, %s) RETURNING id;",
            (data['pickup'], data['destination'], 'new')
        )
        order_id = cursor.fetchone()[0]
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'order_id': order_id}), 201
    except psycopg2.Error as e:
        logger.error(f"Ошибка базы данных: {e}")
        return jsonify({'error': 'Failed to create order'}), 500
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT o.id, o.pickup, o.destination, o.status, d.name AS driver_name
            FROM orders o
            LEFT JOIN drivers d ON o.driver_id = d.id
            WHERE o.id = %s;
        """, (order_id,))
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
