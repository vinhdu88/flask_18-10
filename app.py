from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
app = Flask(__name__)
sqldbname = 'db/website.db'
app.secret_key = 'mysecretkey'

@app.route('/')
@app.route('/home')
def index():
    if 'current_user' in session: 
        current_username = session['current_user']['name']
    else:
        current_username = ''

    
    return render_template('home.html', user_name = current_username)


def load_data_from_db(search_text):
    if search_text: 
        conn = sqlite3.connect(sqldbname)
        cursor = conn.cursor()
        sqlcommand = f'select * from storages where model like "%{search_text}%"'
        cursor.execute(sqlcommand)
        data = cursor.fetchall()
        conn.close()
        return data

@app.route('/searchData', methods = ['POST'])
def searchData():
    if 'current_user' in session:
        current_username = session['current_user']['name']
    else:
        current_username = ''
    search_text = request.form['searchInput']
    products = load_data_from_db(search_text)
    return render_template('home.html', search_text = search_text, products = products, user_name = current_username)


@app.route('/cart/add', methods = ['POST'])
def add_to_cart():
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    connection = sqlite3.connect(sqldbname)
    cursor = connection.cursor()
    cursor.execute( f'select model, price from storages where id = {product_id}')
    product = cursor.fetchone()
    connection.close()
    product_dict = {
        "id":product_id,
        "name": product[0],
        "price": product[1],
        "quantity": quantity
    }   
    cart = session.get('cart', [])
    found = False
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += quantity
            found = True
            break
    if not found:
        cart.append(product_dict)
    session['cart'] = cart

    rows = len(cart)
    outputmessage = (f'Product added to cart successfully!'
                     f'<br>Current {str(rows)} Products'
                     f'<br>Continue search! <a href="{{ url_for("index") }}">Search Page</a>'
                     f'<br>Go to cart! <a href="{{ url_for("view_cart") }}">Cart Page</a>')
    return outputmessage
        
@app.route('/viewcart', methods = ['POST', 'GET'])
def view_cart():
    current_cart = []
    if 'cart' in session:
        current_cart = session.get('cart', [])
    if 'current_user' in session:
        current_username = session['current_user']['name']
    else:
        current_username = ''
    return render_template('cart.html', carts = current_cart, user_name = current_username)

@app.route('/update_cart', methods = ['POST'])
def update_cart():
    cart = session.get('cart', [])
    new_cart = []
    for product in cart:
        product_id = str(product['id'])
        if f'quantity-{product_id}' in request.form: 
            quantity = int(request.form[f'quantity-{product_id}'])
            if quantity == 0 or f'delete-{product_id}' in request.form:
                continue
            product['quantity'] = quantity
        new_cart.append(product)
    session['cart'] = new_cart
    return redirect(url_for('view_cart'))

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['txt-username']
        password = request.form['txt-password']
        obj_user = get_obj_user(username, password)
        if int(obj_user[0])>0:
            obj_user = {
                "id":obj_user[0],
                "name":obj_user[1],
                "email":obj_user[2]
            }
            session['current_user'] = obj_user
        return redirect(url_for('index'))
    return render_template('login.html')
def get_obj_user(username, password):
    result = []
    sqldbname = 'db/website.db'
    conn = sqlite3.connect(sqldbname)
    cursor = conn.cursor()
    sqlcommand = 'select * from user where name=? and password = ?'
    cursor.execute(sqlcommand, (username, password))
    obj_user = cursor.fetchone()
    if len(obj_user) > 0:
        result = obj_user
    conn.close()
    return result

@app.route('/proceed_cart', methods = ['POST', 'GET'])
def proceed_cart():
    if 'current_user' in session:
        user_id = session['current_user']['id']
        user_email = session['current_user']['email']
    else:
        user_id = 0
    current_cart = []
    if 'cart' in session:
        shopping_cart = session.get('cart', [])
        sqldbname = 'db/website.db'
        conn = sqlite3.connect(sqldbname)
        cursor = conn.cursor()
        user_address = "User Address"
        user_mobile = "User Mobile"
        purchase_date = "2024-10-18"
        ship_date = "2024-10-20"
        status = 1
        cursor.execute('insert into "orders" (user_id, user_email, user_address, user_mobile, purchase_date, ship_date, status) values (?,?,?,?,?,?,?)', (user_id, user_email, user_address, user_mobile, purchase_date, ship_date, status))
        order_id = cursor.lastrowid
        print(order_id)
        conn.commit()
        conn.close()
    conn = sqlite3.connect(sqldbname)
    cursor = conn.cursor()
    for product in shopping_cart:
        product_id = product['id']
        price = product['price']
        quantity = product['quantity']
        cursor.execute('insert into order_details (order_id, product_id, price, quantity) values (?,?,?,?)', (order_id, product_id, price, quantity))
        conn.commit()
        conn.close()
    if 'cart' in session:
        current_cart = session.pop('cart', [])
    else:
        print("No current cart in session") 
    order_url = url_for('orders', order_id = order_id, _external = True)
    return f'Redirecting to order page : <a href="{order_url}">{order_url}</a>'

@app.route('/orders/<int:order_id>' , methods = ['GET'])
def orders(order_id):
    sqldbname = 'db/website.db'
    user_id = session.get('current_user', {}).get('id')
    if user_id:
        conn = sqlite3.connect(sqldbname)
        cursor = conn.cursor()
        if order_id is not None:
            cursor.execute('select * from orders where id = ? and user_id = ?', (order_id,user_id))
            order = cursor.fetchone()
            cursor.execute('select * from order_details where order_id = ?', (order_id,))
            order_details = cursor.fetchall()
            conn.close()
            return render_template('order_details.html', order = order, order_details = order_details)
        else:
            cursor.execute('select * from orders where user_id = ?', (user_id,))
            user_orders = cursor.fetchall()
            conn.close()
            return render_template('orders.html', orders = user_orders)
    return "user not logged in"





if __name__ == "__main__":
    app.run(debug=True)