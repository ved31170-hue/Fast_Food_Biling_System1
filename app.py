from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY,
        item TEXT,
        qty INTEGER,
        total INTEGER,
        status TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN ----------
USERNAME = "admin"
PASSWORD = "1234"

# ---------- MENU ----------
menu_items = [
    {"name": "Burger", "price": 120, "img": "burger.jpg"},
    {"name": "Pizza", "price": 250, "img": "pizza.jfif"},
    {"name": "Fries", "price": 80, "img": "fries.jfif"},
    {"name": "Coke", "price": 50, "img": "coke.jfif"},
    {"name": "Pasta", "price": 180, "img": "pasta.jfif"},
    {"name": "Noodles", "price": 140, "img": "noodles.jfif"},
    {"name": "Momos", "price": 120, "img": "momos.jfif"},
    {"name": "Sandwich", "price": 100, "img": "sandwich.jfif"},
    {"name": "Milkshake", "price": 130, "img": "milkshake.jfif"},
    {"name": "Ice Cream", "price": 90, "img": "icecream.jfif"},
    {"name": "Coffee", "price": 60, "img": "coffe.jfif"},
    {"name": "Tea", "price": 40, "img": "tea.jfif"},
    {"name": "Paneer Roll", "price": 140, "img": "paneerroll.jfif"},
    {"name": "Brownie", "price": 110, "img": "brownie.jfif"},
    {"name": "Soup", "price": 90, "img": "soup.jfif"},
    {"name": "Salad", "price": 100, "img": "salad.jfif"},
    {"name": "Hotdog", "price": 110, "img": "hotdog.jfif"},
    {"name": "Nachos", "price": 150, "img": "nachos.jfif"},
    {"name": "Donut", "price": 70, "img": "donut.jfif"},
    {"name": "Wrap", "price": 130, "img": "wrap.jfif"}
]

# ---------- ROUTES ----------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("menu.html", items=menu_items)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["user"] = "admin"
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/add", methods=["POST"])
def add():
    cart = session.get("cart", [])

    qty = int(request.form["qty"])
    price = int(request.form["price"])

    cart.append({
        "name": request.form["name"],
        "price": price,
        "qty": qty,
        "total": price * qty
    })

    session["cart"] = cart
    return redirect("/cart")

@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(i["total"] for i in cart)
    return render_template("cart.html", cart=cart, total=total)

@app.route("/bill")
def bill():
    cart = session.get("cart", [])

    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()

    for item in cart:
        cur.execute("""
        INSERT INTO orders(item, qty, total, status, date)
        VALUES (?,?,?,?,?)
        """, (
            item["name"],
            item["qty"],
            item["total"],
            "Pending",
            datetime.now().strftime("%Y-%m-%d")
        ))

    conn.commit()
    conn.close()

    return render_template("bill.html", cart=cart)

@app.route("/download")
def download():
    file = "bill.pdf"
    c = canvas.Canvas(file)

    y = 800
    c.drawString(100, y, "Restaurant Bill")
    y -= 30

    cart = session.get("cart", [])
    total = 0

    for item in cart:
        c.drawString(100, y, f"{item['name']} x{item['qty']} - ₹{item['total']}")
        total += item["total"]
        y -= 20

    c.drawString(100, y-20, f"Total: ₹{total}")
    c.save()

    return send_file(file, as_attachment=True)

@app.route("/orders")
def orders():
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders")
    data = cur.fetchall()
    conn.close()
    return render_template("orders.html", orders=data)

@app.route("/complete/<int:id>")
def complete(id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='Completed' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/orders")

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()

    cur.execute("SELECT date, SUM(total) FROM orders GROUP BY date")
    data = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]

    cur.execute("SELECT SUM(total) FROM orders")
    revenue = cur.fetchone()[0] or 0

    conn.close()

    labels = [i[0] for i in data]
    values = [i[1] for i in data]

    return render_template("dashboard.html",
                           labels=labels,
                           values=values,
                           total_orders=total_orders,
                           revenue=revenue)

if __name__ == "__main__":
    app.run(debug=True)