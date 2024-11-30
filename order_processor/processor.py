import time
import psycopg2 # type: ignore
from psycopg2.extras import RealDictCursor # type: ignore
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(
        host="database",
        database="taxi_service",
        user="user",
        password="pass"
    )

def assign_driver_to_order(order_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Выбираем первого доступного водителя с блокировкой строки
        cursor.execute("SELECT id, name FROM drivers WHERE status = %s FOR UPDATE SKIP LOCKED LIMIT 1;", ('available',))
        driver = cursor.fetchone()

        if driver:
            driver_id = driver[0]
            # Обновляем заказ и водителя
            cursor.execute("UPDATE orders SET driver_id = %s, status = %s WHERE id = %s;", 
                           (driver_id, 'in_progress', order_id))
            cursor.execute("UPDATE drivers SET status = %s WHERE id = %s;", ('busy', driver_id))
            connection.commit()
            logger.info(f"Driver {driver_id} assigned to order {order_id}")
            return driver_id
        else:
            # Если доступных водителей нет
            cursor.execute("UPDATE orders SET status = %s WHERE id = %s;", ('wait_taxi', order_id))
            connection.commit()
            logger.info(f"No drivers available for order {order_id}")
            return None
    except Exception as e:
        connection.rollback()
        logger.error(f"Error assigning driver: {e}")
    finally:
        cursor.close()
        connection.close()


def complete_order(order_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Обновляем статус заказа на "completed"
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s;", ('completed', order_id))

        # Освобождаем водителя
        cursor.execute("SELECT driver_id FROM orders WHERE id = %s;", (order_id,))
        driver_id = cursor.fetchone()
        
        if driver_id:
            driver_id = driver_id[0]
            cursor.execute("UPDATE drivers SET status = %s WHERE id = %s;", ('available', driver_id))
            connection.commit()
            logger.info(f"Order {order_id} completed. Driver {driver_id} is now available.")
        else:
            logger.warning(f"No driver assigned for order {order_id}.")
            connection.commit()

    except Exception as e:
        connection.rollback()
        logger.error(f"Error completing order {order_id}: {e}")
    finally:
        cursor.close()
        connection.close()

def process_order(order):
    """Обработка одного заказа."""
    order_id = order['id']
    driver_id = assign_driver_to_order(order_id)
    if driver_id:
        # Имитируем выполнение заказа
        logger.info(f"Processing order {order_id}...")
        time.sleep(30)  # Задержка, имитирующая обработку заказа
        complete_order(order_id)
        logger.info(f"Order {order_id} processing completed.")

def process_orders():
    while True:
        try:
            connection = get_db_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            # Получаем заказы со статусом "new"
            cursor.execute("SELECT id FROM orders WHERE status = %s;", ('new',))
            orders = cursor.fetchall()
            cursor.close()
            connection.close()

            if orders:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    # Запускаем обработку заказов параллельно
                    futures = [executor.submit(process_order, order) for order in orders]

                    # Обработка завершения задач
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error during order processing: {e}")

            else:
                logger.info("No new orders found. Sleeping for 5 seconds.")
                time.sleep(5)

        except Exception as e:
            logger.error(f"Error in process_orders: {e}")
            time.sleep(5)

if __name__ == "__main__":
    logger.info("Starting order processor...")
    process_orders()
