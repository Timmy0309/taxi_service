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
            alert(`Your order number is: ${data.order_number}`);
            pollOrderStatus(data.order_id);
        } else {
            const error = await response.json();
            document.getElementById('responseMessage').textContent = `Error: ${error.error}`;
        }
    } catch (error) {
        document.getElementById('responseMessage').textContent = `Failed to send order: ${error.message}`;
    }
});

async function pollOrderStatus(orderId) {
    try {
        const response = await fetch(`http://localhost:5000/orders/${orderId}`);
        if (response.ok) {
            const order = await response.json();
            document.getElementById('responseMessage').textContent = `
                Order Details:
                ID: ${order.id}
                Pickup: ${order.pickup}
                Destination: ${order.destination}
                Status: ${order.status}
                ${order.driver_name ? `Driver: ${order.driver_name}` : 'Waiting for a driver...'}
            `;

            if (order.status !== 'completed') {
                setTimeout(() => pollOrderStatus(orderId), 5000);
            }
        } else {
            document.getElementById('responseMessage').textContent = `Failed to fetch order details.`;
        }
    } catch (error) {
        document.getElementById('responseMessage').textContent = `Error: ${error.message}`;
    }
}

async function orderStatus(orderNumber) {
    try {
        const response = await fetch(`http://localhost:5000/orders/number/${orderNumber}`);
        if (response.ok) {
            const order = await response.json();
            document.getElementById('orderDetails').textContent = `
                Order Details:
                ID: ${order.id}
                Pickup: ${order.pickup}
                Destination: ${order.destination}
                Status: ${order.status}
                ${order.driver_name ? `Driver: ${order.driver_name}` : 'Waiting for a driver...'}
            `;

            if (order.status !== 'completed') {
                setTimeout(() => orderStatus(orderNumber), 5000);
            }
        } else {
            document.getElementById('orderDetails').textContent = `Order not found.`;
        }
    } catch (error) {
        document.getElementById('orderDetails').textContent = `Error: ${error.message}`;
    }
}

document.getElementById('searchOrderForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const orderNumber = document.getElementById('orderNumber').value;
    orderStatus(orderNumber);
    
});

