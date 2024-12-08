import asyncio
import psycopg2 # type: ignore
from psycopg2.extras import RealDictCursor # type: ignore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_db_connection():
    """Возвращает асинхронное подключение к базе данных."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: psycopg2.connect(
            host="database",
            database="taxi_service",
            user="user",
            password="pass"
        )
    )

async def assign_driver_to_order(order_id):
    """Назначает водителя на заказ, если доступен."""
    connection = await get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("BEGIN;")
        cursor.execute(
            "SELECT id, name FROM drivers WHERE status = %s FOR UPDATE SKIP LOCKED LIMIT 1;",
            ('available',)
        )
        driver = cursor.fetchone()

        if driver:
            driver_id = driver[0]
            cursor.execute(
                "UPDATE orders SET driver_id = %s, status = %s WHERE id = %s;",
                (driver_id, 'выполняется', order_id)
            )
            cursor.execute("UPDATE drivers SET status = %s WHERE id = %s;", ('busy', driver_id))
            connection.commit()
            logger.info(f"Driver {driver_id} assigned to order {order_id}")
            return driver_id
        else:
            cursor.execute("UPDATE orders SET status = %s WHERE id = %s;", ('Ожидание свободного таксиста', order_id))
            connection.commit()
            logger.info(f"No drivers available for order {order_id}, will retry later.")
            return None
    except Exception as e:
        connection.rollback()
        logger.error(f"Error assigning driver: {e}")
    finally:
        cursor.close()
        connection.close()

async def complete_order(order_id):
    """Завершает заказ и освобождает водителя."""
    connection = await get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s;", ('Завершен', order_id))
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

async def simulate_order_processing(order_id, delay=30):
    """Имитирует выполнение заказа."""
    logger.info(f"Processing order {order_id}...")
    await asyncio.sleep(delay)
    logger.info(f"Order {order_id} processing completed.")

async def process_order(order):
    """Обрабатывает один заказ."""
    order_id = order['id']
    driver_id = await assign_driver_to_order(order_id)
    if driver_id:
        await simulate_order_processing(order_id)
        await complete_order(order_id)

async def fetch_new_orders(queue):
    """Периодически проверяет новые заказы и добавляет их в очередь."""
    while True:
        try:
            connection = await get_db_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT id FROM orders WHERE status = %s OR status = %s;", ('новый заказ', 'wait_taxi'))
            orders = cursor.fetchall()
            cursor.close()
            connection.close()

            for order in orders:
                connection = await get_db_connection()
                cursor = connection.cursor()
                cursor.execute("UPDATE orders SET status = %s WHERE id = %s;", ('queued', order['id']))
                connection.commit()
                cursor.close()
                connection.close()

                await queue.put(order)

            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error fetching new orders: {e}")
            await asyncio.sleep(5)

async def process_orders(queue):
    """Обрабатывает заказы из очереди параллельно."""
    while True:
        order = await queue.get()
        asyncio.create_task(process_order(order))
        queue.task_done()

async def main():
    """Основная функция."""
    queue = asyncio.Queue()

    fetch_task = asyncio.create_task(fetch_new_orders(queue))
    process_task = asyncio.create_task(process_orders(queue))

    await asyncio.gather(fetch_task, process_task)

if __name__ == "__main__":
    logger.info("Starting order processor...")
    asyncio.run(main())
