const productList = [
    {
        vendor: "Juana's Handicrafts",
        name: "Handwoven Bag",
        price: 1000.00,
        quantity: 1
    },
    {
        vendor: "Mary's Handicrafts",
        name: "Handwoven Bag",
        price: 1000.00,
        quantity: 2
    },
    {
        vendor: "Mary's Handicrafts",
        name: "Handwoven Bag",
        price: 1000.00,
        quantity: 1
    }
];

let selectedPaymentMethod = 'GCash'; // Initialize with 'GCash' as default

function populateProducts() {
    const productListContainer = document.getElementById("product-list");
    productListContainer.innerHTML = ""; // Clear existing content

    const merchantList = [];
    productList.forEach(product => {
        if (!merchantList.includes(product.vendor)) {
            merchantList.push(product.vendor);
        }
    });

    productList.forEach((product, index) => {
        const itemSubtotal = product.price * product.quantity;

        const productItem = document.createElement("div");
        productItem.classList.add("product-item");

        productItem.innerHTML = `
            <div class="product-image"></div>
            <div class="product-details">
                <div class="product-name">${product.vendor}</div>
                <div class="product-price">${product.name}</div>
            </div>
            <div class="unit-price">Php ${product.price.toFixed(2)}</div>
            <div class="quantity">${product.quantity}</div>
            <div class="item-subtotal">Php ${itemSubtotal.toFixed(2)}</div>
        `;

        productListContainer.appendChild(productItem);

        if (merchantList.length > 1 && index < productList.length - 1 && product.vendor !== productList[index + 1].vendor) {
            const separator = document.createElement("div");
            separator.classList.add("merchant-separator");
            productListContainer.appendChild(separator);
        }
    });
}

function selectPayment(paymentMethod) {
    // Remove 'active' class from the previously selected button
    const paymentButtons = document.querySelectorAll('.payment-button');
    paymentButtons.forEach(button => button.classList.remove('active'));

    // Add 'active' class to the clicked button
    const clickedButton = document.querySelector(`.payment-button[onclick="selectPayment('${paymentMethod}')"]`);
    if (clickedButton) {
        clickedButton.classList.add('active');
    }

    selectedPaymentMethod = paymentMethod;
    console.log(`Selected payment method: ${selectedPaymentMethod}`);
}

function changeAddress() {
    alert("Change address functionality will be implemented here.");
}

function placeOrder() {
    alert(`Placing order with payment method: ${selectedPaymentMethod}`);
}

// Call functions
populateProducts();