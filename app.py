from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime, timedelta, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'MySQLhello#1',
    'database': 'medicine_shop'
}

def get_db_connection():
    """Helper method to get a database connection and dictionary cursor"""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    return connection, cursor


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn, cursor = get_db_connection()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    try:
        conn, cursor = get_db_connection()
        
        cursor.execute("SELECT COUNT(*) as count FROM medicines")
        total_medicines = cursor.fetchone()['count']
        
        cursor.execute("SELECT SUM(total_price) as total_revenue FROM sales")
        revenue_result = cursor.fetchone()
        total_sales_revenue = revenue_result['total_revenue'] if revenue_result['total_revenue'] else 0.0
        

        cursor.execute("SELECT * FROM dashboard_view")
        dashboard_data = cursor.fetchall()
        
        low_stock = []
        expired = []
        
        today = date.today()
        thirty_days = today + timedelta(days=30)
        
        for med in dashboard_data:
            if med['quantity'] < 10:
                low_stock.append(med)
            expiry = med['expiry_date']
            if isinstance(expiry, datetime):
                expiry = expiry.date()
            if expiry <= thirty_days:
                expired.append(med)
        
        conn.close()
        return render_template('index.html', 
                               total_medicines=total_medicines, 
                               total_sales_revenue=total_sales_revenue,
                               low_stock=low_stock,
                               expired=expired)
    except mysql.connector.Error as err:
        flash(f"Database error: {err}. Please ensure MySQL is running and the database 'medicine_shop' exists.", "danger")
        return render_template('index.html', total_medicines=0, total_sales_revenue=0.0)


@app.route('/medicines')
@login_required
def medicines():
    search_query = request.args.get('search', '')
    conn, cursor = get_db_connection()
    
    if search_query:
        cursor.execute("SELECT * FROM medicines WHERE name LIKE %s ORDER BY id DESC", ('%' + search_query + '%',))
    else:
        cursor.execute("SELECT * FROM medicines ORDER BY id DESC")
        
    medicines_list = cursor.fetchall()
    conn.close()
    return render_template('medicines.html', medicines=medicines_list, search_query=search_query)


@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        quantity = request.form['quantity']
        expiry_date = request.form['expiry_date']
        
        conn, cursor = get_db_connection()
        cursor.execute("""
            INSERT INTO medicines (name, category, price, quantity, expiry_date) 
            VALUES (%s, %s, %s, %s, %s)
        """, (name, category, price, quantity, expiry_date))
        conn.commit()
        conn.close()
        
        flash('Medicine added successfully!', 'success')
        return redirect(url_for('medicines'))
        
    return render_template('add_medicine.html')


@app.route('/edit_medicine/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(id):
    conn, cursor = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        quantity = request.form['quantity']
        expiry_date = request.form['expiry_date']
        
        cursor.execute("""
            UPDATE medicines 
            SET name=%s, category=%s, price=%s, quantity=%s, expiry_date=%s
            WHERE id=%s
        """, (name, category, price, quantity, expiry_date, id))
        conn.commit()
        conn.close()
        
        flash('Medicine updated successfully!', 'success')
        return redirect(url_for('medicines'))
        
    else:
        cursor.execute("SELECT * FROM medicines WHERE id=%s", (id,))
        medicine = cursor.fetchone()
        conn.close()
        
        if not medicine:
            flash('Medicine not found!', 'danger')
            return redirect(url_for('medicines'))
            
        return render_template('edit_medicine.html', medicine=medicine)


@app.route('/delete_medicine/<int:id>')
@login_required
def delete_medicine(id):
    conn, cursor = get_db_connection()
    cursor.execute("DELETE FROM medicines WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    
    flash('Medicine deleted successfully!', 'success')
    return redirect(url_for('medicines'))


@app.route('/sales')
@login_required
def sales():
    conn, cursor = get_db_connection()
    cursor.execute("""
        SELECT s.sale_id, m.name as medicine_name, s.quantity, s.total_price, s.date 
        FROM sales s 
        JOIN medicines m ON s.medicine_id = m.id 
        ORDER BY s.date DESC
    """)
    sales_list = cursor.fetchall()
    conn.close()
    return render_template('sales.html', sales=sales_list)


@app.route('/sell_medicine/<int:id>', methods=['GET', 'POST'])
@login_required
def sell_medicine(id):
    conn, cursor = get_db_connection()
    
    cursor.execute("SELECT * FROM medicines WHERE id=%s", (id,))
    medicine = cursor.fetchone()
    
    if not medicine:
        flash('Medicine not found!', 'danger')
        conn.close()
        return redirect(url_for('medicines'))
        
    if request.method == 'POST':
        sell_quantity = int(request.form['quantity'])
        
        total_price = sell_quantity * medicine['price']
        
        try:
            cursor.callproc('sell_medicine', (id, sell_quantity))
            conn.commit()
            
            flash('Sale successful!', 'success')
            
            bill_data = {
                'medicine_name': medicine['name'],
                'quantity': sell_quantity,
                'unit_price': medicine['price'],
                'total_price': total_price
            }
            conn.close()
            return render_template('bill.html', bill_data=bill_data)
            
        except mysql.connector.Error as err:
            flash(f"Sale failed: {err.msg}", 'danger')
            conn.close()
            return redirect(url_for('sell_medicine', id=id))
        
    conn.close()
    return render_template('sell_medicine.html', medicine=medicine)

if __name__ == '__main__':
    app.run(debug=True)
