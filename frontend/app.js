
const searchOrderForm = document.getElementById('searchOrderForm');
const orderDetails = document.getElementById('orderDetails');
const pickupLocationElem = document.getElementById('pickupLocation');
const destinationElem = document.getElementById('destinationLocation');
const statusElem = document.getElementById('status');
const driverNameElem = document.getElementById('driverName');

let currentOrderNumber = null;

document.getElementById('orderForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const pickup = document.getElementById('pickup').value;
    const destination = document.getElementById('destination').value;

    try {
        const response = await fetch('http://localhost:5000/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pickup, destination })
        });

        if (response.ok) {
            const data = await response.json();
            console.log(data);
            const orderNum = data.order_number;
            showCustomAlert(`Ваш номер заказа: ${orderNum}`, orderNum);
        } else {
            const error = await response.json();
            document.querySelector('error').textContent = `Ошибка: ${error.error}`;
        }
    } catch (error) {
        document.querySelector('error').textContent = `Не удалось отправить заказ: ${error.message}`;
    }
});


async function orderStatus(orderNumber) {
    if (orderNumber !== currentOrderNumber) return;

    try {
        const response = await fetch(`http://localhost:5000/orders/number/${orderNumber}`);
        if (response.ok) {
            const order = await response.json();

            if (order && order.id) {
                pickupLocationElem.textContent = order.pickup;
                destinationElem.textContent = order.destination;
                statusElem.textContent = order.status;
                driverNameElem.textContent = order.driver_name || 'Пока не назначен';

                orderDetails.classList.remove('hidden');
            } else {
                document.querySelector('.error').classList.remove('hidden');
                document.querySelector('.error').textContent = `Заказ не найден.`;
            }

            if (order.status !== 'completed' && orderNumber === currentOrderNumber) {
                setTimeout(() => orderStatus(orderNumber), 5000);
            }
        } else {
            document.querySelector('.error').classList.remove('hidden');
            document.querySelector('.error').textContent = `Заказ не найден.`;
        }
    } catch (error) {
        document.querySelector('.error').classList.remove('hidden');
        document.querySelector('.error').textContent = `Не удалось получить данные о заказе. ${error.message}`;
    }
}


document.getElementById('searchOrderForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const orderNumber = document.getElementById('orderNumber').value;

    currentOrderNumber = orderNumber;

    document.querySelector('.error').classList.add('hidden');
    orderDetails.classList.add('hidden');

    orderStatus(orderNumber);
});


function showCustomAlert(message, orderNumber = '') {
    const alertBox = document.getElementById('customAlert');
    const alertMessage = document.getElementById('alertMessage');
    const closeAlert = document.getElementById('closeAlert');
    const fillOrderNumber = document.getElementById('fillOrderNumber');
    const orderNumberField = document.getElementById('orderNumber');

    alertMessage.textContent = message;

    alertBox.classList.remove('hidden');

    if (orderNumber) {
        fillOrderNumber.style.display = 'inline-block';
        fillOrderNumber.onclick = () => {
            orderNumberField.value = orderNumber;
            alertBox.classList.add('hidden');
        };
    } else {
        fillOrderNumber.style.display = 'none';
    }

    closeAlert.onclick = () => {
        console.log('Close button clicked');
        alertBox.classList.add('hidden');
    };
}
