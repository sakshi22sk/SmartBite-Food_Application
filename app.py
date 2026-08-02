from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

import psycopg2
from google import genai
from config import Config

from google import genai
import os

app = Flask(__name__)

# ==========================================
# CONFIG
# ==========================================

app.secret_key = Config.SECRET_KEY
client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)


# ==========================================
# DATABASE
# ==========================================

def get_connection():

    return psycopg2.connect(

        host=Config.DB_HOST,

        database=Config.DB_NAME,

        user=Config.DB_USER,

        password=Config.DB_PASSWORD,

        port=Config.DB_PORT

    )


# ==========================================
# SESSION CART
# ==========================================

def get_cart():

    if "cart" not in session:

        session["cart"] = {}

    return session["cart"]


def save_cart(cart):

    session["cart"] = cart

    session.modified = True


def cart_count():

    cart = get_cart()

    total = 0

    for item in cart.values():

        total += item["qty"]

    return total


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""

        SELECT *

        FROM food

        WHERE available=TRUE

        ORDER BY rating DESC

        LIMIT 6

    """)

    foods = cur.fetchall()

    cur.close()

    conn.close()

    return render_template(

        "index.html",

        foods=foods,

        cart_count=cart_count()

    )


# ==========================================
# MENU
# ==========================================

@app.route("/menu")
def menu():

    search = request.args.get("search", "").strip()

    veg = request.args.get("veg", "")

    category = request.args.get("category", "")

    sort = request.args.get("sort", "")

    sql = """

        SELECT *

        FROM food

        WHERE available=TRUE

    """

    values = []

    if search:

        sql += """

        AND (

            LOWER(name) LIKE LOWER(%s)

            OR LOWER(description) LIKE LOWER(%s)

            OR LOWER(category) LIKE LOWER(%s)

        )

        """

        values.extend([

            f"%{search}%",

            f"%{search}%",

            f"%{search}%"

        ])

    if veg == "veg":

        sql += " AND veg=TRUE "

    elif veg == "nonveg":

        sql += " AND veg=FALSE "

    if category:

        sql += " AND category=%s "

        values.append(category)

    if sort == "price_low":

        sql += " ORDER BY price ASC "

    elif sort == "price_high":

        sql += " ORDER BY price DESC "

    elif sort == "rating":

        sql += " ORDER BY rating DESC "

    elif sort == "time":

        sql += " ORDER BY prep_time ASC "

    else:

        sql += " ORDER BY id "

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(sql, values)

    foods = cur.fetchall()

    cur.execute("""

        SELECT DISTINCT category

        FROM food

        ORDER BY category

    """)

    categories = cur.fetchall()

    cur.close()

    conn.close()

    return render_template(

        "menu.html",

        foods=foods,

        categories=categories,

        cart_count=cart_count(),

        selected_category=category,

        selected_sort=sort,

        selected_veg=veg,

        search=search

    )
# ==========================================
# CART APIs
# ==========================================

@app.route("/cart/add/<int:food_id>", methods=["POST"])
def add_to_cart(food_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id,name,price,image
        FROM food
        WHERE id=%s
    """,(food_id,))

    food = cur.fetchone()

    cur.close()
    conn.close()

    if not food:
        return jsonify({"success":False})

    cart = get_cart()

    key = str(food_id)

    if key in cart:

        cart[key]["qty"] += 1

    else:

        cart[key] = {

            "id":food[0],
            "name":food[1],
            "price":float(food[2]),
            "image":food[3],
            "qty":1

        }

    save_cart(cart)

    return jsonify({

        "success":True,

        "count":cart_count(),

        "quantity":cart[key]["qty"]

    })


@app.route("/cart/increase/<int:food_id>",methods=["POST"])
def increase_cart(food_id):

    cart=get_cart()

    key=str(food_id)

    if key in cart:

        cart[key]["qty"]+=1

    save_cart(cart)

    return jsonify({

        "success":True,

        "quantity":cart[key]["qty"],

        "count":cart_count()

    })


@app.route("/cart/decrease/<int:food_id>",methods=["POST"])
def decrease_cart(food_id):

    cart=get_cart()

    key=str(food_id)

    if key in cart:

        cart[key]["qty"]-=1

        if cart[key]["qty"]<=0:

            del cart[key]

            save_cart(cart)

            return jsonify({

                "quantity":0,

                "count":cart_count()

            })

    save_cart(cart)

    return jsonify({

        "quantity":cart[key]["qty"],

        "count":cart_count()

    })


@app.route("/cart/remove/<int:food_id>",methods=["POST"])
def remove_cart(food_id):

    cart=get_cart()

    key=str(food_id)

    if key in cart:

        del cart[key]

    save_cart(cart)

    return jsonify({

        "success":True,

        "count":cart_count()

    })


@app.route("/cart/clear",methods=["POST"])
def clear_cart():

    session["cart"]={}

    session.modified=True

    return jsonify({

        "success":True

    })


# ==========================================
# CART PAGE
# ==========================================

@app.route("/cart")
def cart():

    cart=get_cart()

    subtotal=0

    for item in cart.values():

        subtotal += item["price"]*item["qty"]

    gst=round(subtotal*0.05,2)

    delivery=40 if subtotal>0 else 0

    total=subtotal+gst+delivery

    return render_template(

        "cart.html",

        cart_items=list(cart.values()),

        subtotal=subtotal,

        gst=gst,

        delivery=delivery,

        total=total,

        cart_count=cart_count()

    )


# ==========================================
# CHECKOUT
# ==========================================
@app.route("/checkout")
def checkout():

    return render_template(
        "checkout.html",
        cart_count=cart_count()
    )
# ==========================================
# PLACE ORDER
# ==========================================
@app.route("/place_order", methods=["POST"])
def place_order():
  

    print("PLACE ORDER ROUTE HIT")

    data = request.get_json()

    print(data)

    data = request.get_json()

    customer = data["customer_name"]
    phone = data["phone"]
    address = data["address"]
    order_type = data["order_type"]
    slot = data["time_slot"]
    total = data["total"]
    items = data["items"]

    conn = get_connection()
    cur = conn.cursor()

    try:

        # -------------------------
        # Create Order
        # -------------------------

        cur.execute(
            """
            INSERT INTO orders
            (
                customer_name,
                phone,
                address,
                order_type,
                time_slot,
                total,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                customer,
                phone,
                address,
                order_type,
                slot,
                total,
                "Preparing"
            )
        )

        order_id = cur.fetchone()[0]

        # -------------------------
        # Save Every Food Item
        # -------------------------

        for item in items:

            cur.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    food_id,
                    food_name,
                    quantity,
                    price,
                    subtotal
                )
                VALUES
                (%s,%s,%s,%s,%s,%s)
                """,
                (
                    order_id,
                    item["id"],
                    item["name"],
                    item["qty"],
                    item["price"],
                    item["qty"] * item["price"]
                )
            )

        conn.commit()

        cur.close()
        conn.close()

        return jsonify({

            "success": True,
            "order_id": order_id

        })

    except Exception as e:

        conn.rollback()

        cur.close()
        conn.close()

        print(e)

        return jsonify({

            "success": False,
            "error": str(e)

        })

# ==========================================
# ORDERS
# ==========================================

@app.route("/orders")
def orders():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM orders
        ORDER BY created_at DESC
    """)

    orders = cur.fetchall()

    all_orders = []

    for order in orders:

        cur.execute("""
            SELECT food_name,
                   quantity,
                   subtotal
            FROM order_items
            WHERE order_id=%s
        """,(order[0],))

        items = cur.fetchall()

        all_orders.append({

            "order": order,

            "items": items

        })

    cur.close()
    conn.close()

    return render_template(

        "orders.html",

        orders=all_orders,

        cart_count=cart_count()

    )


# ==========================================
# DELIVERED
# ==========================================

@app.route("/delivered")
def delivered():

    conn=get_connection()
    cur=conn.cursor()

    cur.execute("""

        SELECT *

        FROM food

        ORDER BY rating DESC

        LIMIT 4

    """)

    addons=cur.fetchall()

    cur.close()
    conn.close()

    return render_template(

        "delivered.html",

        addons=addons,

        cart_count=cart_count()

    )


# ==========================================
# LOCATIONS
# ==========================================

@app.route("/locations")
def locations():

    conn=get_connection()
    cur=conn.cursor()

    cur.execute("""

        SELECT *

        FROM branches

        ORDER BY id

    """)

    branches=cur.fetchall()

    cur.close()
    conn.close()

    return render_template(

        "locations.html",

        branches=branches,

        cart_count=cart_count()

    )


# ==========================================
# ADMIN
# ==========================================

@app.route("/admin")
def admin():

    conn=get_connection()

    cur=conn.cursor()

    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders=cur.fetchall()

    cur.execute("SELECT * FROM food ORDER BY id")
    foods=cur.fetchall()

    cur.execute("""

        SELECT *

        FROM chat_history

        ORDER BY id DESC

        LIMIT 20

    """)

    chats=cur.fetchall()

    cur.close()
    conn.close()

    return render_template(

        "admin.html",

        orders=orders,

        foods=foods,

        chats=chats

    )


@app.route("/update_status",methods=["POST"])
def update_status():

    order_id=request.form["order_id"]
    status=request.form["status"]

    conn=get_connection()
    cur=conn.cursor()

    cur.execute("""

        UPDATE orders

        SET status=%s

        WHERE id=%s

    """,(status,order_id))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"success":True})


@app.route("/delete_order/<int:id>",methods=["POST"])
def delete_order(id):

    conn=get_connection()
    cur=conn.cursor()

    cur.execute("""

        DELETE FROM orders

        WHERE id=%s

    """,(id,))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"success":True})

# ==========================================
# AI CHATBOT
# ==========================================

@app.route("/chatbot")
def chatbot():

    return render_template(
        "chatbot.html",
        cart_count=cart_count()
    )


@app.route("/ask_ai", methods=["POST"])
def ask_ai():

    prompt = request.json["message"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            name,
            price,
            category,
            veg
        FROM food
        WHERE available = TRUE
    """)

    foods = cur.fetchall()

    menu_text = "\n".join([
        f"{f[0]} | ₹{f[1]} | {f[2]} | {'Veg' if f[3] else 'Non Veg'}"
        for f in foods
    ])

    system_prompt = f"""
You are SmartBite AI Chef.

Recommend ONLY foods from this restaurant menu.

Restaurant Menu:
{menu_text}

Customer:
{prompt}

Rules:
- Recommend only items from the menu.
- Mention prices.
- Keep answers short.
- Be friendly.
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=system_prompt
        )

        reply = response.text

        cur.execute("""
            INSERT INTO chat_history
            (user_message, ai_response)
            VALUES (%s, %s)
        """, (prompt, reply))

        conn.commit()

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print(e)

        return jsonify({
            "reply": "❌ Unable to contact SmartBite AI."
        })

    finally:

        cur.close()
        conn.close()


# ==========================================
# FOOD API
# ==========================================

@app.route("/foods")
def foods():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM food
        ORDER BY id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(rows)


# ==========================================
# SEARCH API
# ==========================================

@app.route("/search")
def search():

    keyword = request.args.get("q", "")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM food
        WHERE LOWER(name) LIKE LOWER(%s)
        ORDER BY rating DESC
    """, (f"%{keyword}%",))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(rows)


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)