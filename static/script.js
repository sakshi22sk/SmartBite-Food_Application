/* ==========================================
   SMARTBITE AI
   CART ENGINE
========================================== */

let foods = {};

/* ----------------------------
   CART STORAGE
---------------------------- */

function getCart() {
    return JSON.parse(localStorage.getItem("cart")) || {};
}

function saveCart(cart) {
    localStorage.setItem("cart", JSON.stringify(cart));
}

/* ----------------------------
   CART BADGE
---------------------------- */

function updateCartCount() {

    const badge = document.getElementById("cartCount");

    if (!badge) return;

    const cart = getCart();

    let total = 0;

    Object.values(cart).forEach(item => {
        total += item.qty;
    });

    badge.innerHTML = total;
}

/* ----------------------------
   ADD TO CART
---------------------------- */

function addToCart(id, name, price, image) {

    let cart = getCart();

    if (!cart[id]) {

        cart[id] = {
            id: id,
            name: name,
            price: Number(price),
            image: image,
            qty: 1
        };

    } else {

        cart[id].qty++;

    }

    saveCart(cart);

    updateCard(id);

    updateCartCount();

    if (window.location.pathname.includes("/cart")) {
        loadCart();
    }

}

/* ----------------------------
   INCREASE
---------------------------- */

function increaseQty(id) {

    let cart = getCart();

    if (!cart[id]) return;

    cart[id].qty++;

    saveCart(cart);

    updateCard(id);

    updateCartCount();

    if (window.location.pathname.includes("/cart")) {
        loadCart();
    }

}

/* ----------------------------
   DECREASE
---------------------------- */

function decreaseQty(id) {

    let cart = getCart();

    if (!cart[id]) return;

    cart[id].qty--;

    if (cart[id].qty <= 0) {

        delete cart[id];

    }

    saveCart(cart);

    updateCard(id);

    updateCartCount();

    if (window.location.pathname.includes("/cart")) {
        loadCart();
    }

}

/* ----------------------------
   MENU CARD UPDATE
---------------------------- */

function updateCard(id) {

    const container = document.getElementById("cart-controls-" + id);

    if (!container) return;

    const cart = getCart();

    if (cart[id]) {

        container.innerHTML = `

        <div class="qty-control">

            <button class="qty-btn"
                onclick="decreaseQty(${id})">

                -

            </button>

            <span class="qty-number">

                ${cart[id].qty}

            </span>

            <button class="qty-btn"
                onclick="increaseQty(${id})">

                +

            </button>

        </div>

        `;

    } else {

        const food = foods[id];

        if (!food) return;

        container.innerHTML = `

        <button
            class="btn btn-primary"
            onclick="addToCart(
                ${food.id},
                '${food.name.replace(/'/g, "\\'")}',
                ${food.price},
                '${food.image}'
            )">

            <i class="fas fa-cart-plus"></i>

        </button>

        `;

    }

}

/* ----------------------------
   LOAD ALL FOODS
---------------------------- */

async function loadFoods() {

    try {

        const response = await fetch("/foods");

        const data = await response.json();

        data.forEach(food => {

            foods[food.id] = food;

        });

        refreshCartButtons();

    } catch (err) {

        console.log(err);

    }

}

/* ----------------------------
   REFRESH MENU
---------------------------- */

function refreshCartButtons() {

    const cart = getCart();

    Object.keys(foods).forEach(id => {

        updateCard(id);

    });

    updateCartCount();

}

/* ----------------------------
   PAGE LOAD
---------------------------- */

document.addEventListener("DOMContentLoaded", async () => {

    await loadFoods();

    updateCartCount();

    if (window.location.pathname.includes("/cart")) {

        loadCart();

    }

});
/* ==========================================
   CART PAGE
========================================== */

function loadCart() {

    const cart = getCart();

    const cartContainer = document.getElementById("cartItems");

    if (!cartContainer) return;

    cartContainer.innerHTML = "";

    let subtotal = 0;

    const values = Object.values(cart);

    if (values.length === 0) {

        cartContainer.innerHTML = `

        <div style="
            width:100%;
            text-align:center;
            padding:80px;
            font-size:22px;
            color:#888;
        ">

            🛒 Your cart is empty

            <br><br>

            <a href="/menu">

                <button class="btn btn-primary">

                    Browse Menu

                </button>

            </a>

        </div>

        `;

        updateSummary(0);

        return;
    }

    values.forEach(item => {

        subtotal += item.price * item.qty;

        cartContainer.innerHTML += `

        <div class="cart-card">

            <img
            src="/static/images/${item.image}"
            alt="${item.name}">

            <div class="cart-details">

                <h3>${item.name}</h3>

                <h2>₹${item.price}</h2>

            </div>

            <div class="qty-control">

                <button
                class="qty-btn"
                onclick="decreaseQty(${item.id})">

                -

                </button>

                <span class="qty-number">

                    ${item.qty}

                </span>

                <button
                class="qty-btn"
                onclick="increaseQty(${item.id})">

                +

                </button>

            </div>

            <button

            class="delete-btn"

            onclick="removeItem(${item.id})">

            <i class="fas fa-trash"></i>

            </button>

        </div>

        `;

    });

    updateSummary(subtotal);

}
function removeItem(id){

    let cart = getCart();

    delete cart[id];

    saveCart(cart);

    updateCard(id);

    updateCartCount();

    loadCart();

}
function updateSummary(subtotal){

    const gst = subtotal * 0.05;

    const delivery = subtotal > 0 ? 40 : 0;

    const total = subtotal + gst + delivery;

    const subtotalBox = document.getElementById("subtotal");

    const gstBox = document.getElementById("gst");

    const deliveryBox = document.getElementById("delivery");

    const totalBox = document.getElementById("total");

    if(subtotalBox)
        subtotalBox.innerHTML="₹"+subtotal.toFixed(0);

    if(gstBox)
        gstBox.innerHTML="₹"+gst.toFixed(0);

    if(deliveryBox)
        deliveryBox.innerHTML="₹"+delivery;

    if(totalBox)
        totalBox.innerHTML="₹"+total.toFixed(0);

}
// ================================
// PLACE ORDER
// ================================

async function placeOrder() {

    let cart = JSON.parse(localStorage.getItem("cart")) || {};

    if (Object.keys(cart).length === 0) {

        alert("Your cart is empty.");

        return;
    }

    let subtotal = 0;

    Object.values(cart).forEach(item => {

        subtotal += item.price * item.qty;

    });

    let gst = subtotal * 0.05;

    let total = subtotal + gst + 40;

    const data = {

        customer_name:
            document.getElementById("customerName").value,

        phone:
            document.getElementById("phone").value,

        address:
            document.getElementById("address").value,

        order_type:
            document.getElementById("orderType").value,

        time_slot:
            document.getElementById("timeSlot").value,

        total: total,

        items: Object.values(cart)

    };

    if (
        data.customer_name == "" ||
        data.phone == "" ||
        data.address == ""
    ) {

        alert("Please fill all required details.");

        return;

    }

    const response = await fetch("/place_order", {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify(data)

    });

    const result = await response.json();

    if(result.success){

        localStorage.removeItem("cart");

        alert("🎉 Order Placed Successfully!");

        window.location.href="/orders";

    }

    else{

        alert("Something went wrong.");

    }

}