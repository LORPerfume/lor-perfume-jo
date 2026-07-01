import os
import sqlite3
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'lor-change-this-secret')
os.makedirs(app.instance_path, exist_ok=True)
DB_PATH = os.path.join(app.instance_path, 'app.db')

ORDER_STATUSES = [
    'جديد', 'قيد التجهيز', 'مع شركة التوصيل', 'تم التسليم', 'مرتجع', 'ملغي'
]
PAYMENT_METHODS = [
    'كاش', 'كليك', 'حوالة بنكية', 'شركة التوصيل', 'بطاقة', 'أخرى'
]
MOVEMENT_TYPES = ['إدخال', 'إخراج', 'مرتجع']


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS delivery_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            phone TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            sku TEXT,
            cost REAL NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            order_text TEXT NOT NULL,
            product_id INTEGER,
            quantity INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL,
            cost REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            delivery_company_id INTEGER,
            delivery_receivable REAL NOT NULL DEFAULT 0,
            paid_to_lor REAL NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            delivered_at TEXT,
            returned_at TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(delivery_company_id) REFERENCES delivery_companies(id)
        );

        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL DEFAULT 0,
            reference TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        ''')


def money(value):
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return '0.00'


app.jinja_env.filters['money'] = money


def today_iso():
    return date.today().isoformat()


def now_iso():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def fetch_one(query, params=()):
    with get_db() as db:
        return db.execute(query, params).fetchone()


def fetch_all(query, params=()):
    with get_db() as db:
        return db.execute(query, params).fetchall()


def update_product_quantity(db, product_id, delta):
    if product_id and delta:
        db.execute('UPDATE products SET quantity = quantity + ? WHERE id = ?', (delta, product_id))


def apply_status_effect(db, order, old_status, new_status):
    product_id = order['product_id']
    qty = int(order['quantity'] or 1)
    price = float(order['price'] or 0)
    delivery_company_id = order['delivery_company_id']

    if old_status != 'تم التسليم' and new_status == 'تم التسليم':
        if product_id:
            update_product_quantity(db, product_id, -qty)
            db.execute('''INSERT INTO inventory_movements (product_id, movement_type, quantity, unit_cost, reference, notes, created_at)
                          VALUES (?, 'إخراج', ?, ?, ?, ?, ?)''',
                       (product_id, qty, order['cost'] or 0, f"طلب رقم {order['id']}", 'تم التسليم', now_iso()))
        receivable = price if order['payment_method'] == 'شركة التوصيل' and delivery_company_id else 0
        db.execute('UPDATE orders SET delivery_receivable=?, delivered_at=? WHERE id=?', (receivable, now_iso(), order['id']))

    if old_status == 'تم التسليم' and new_status == 'مرتجع':
        if product_id:
            update_product_quantity(db, product_id, qty)
            db.execute('''INSERT INTO inventory_movements (product_id, movement_type, quantity, unit_cost, reference, notes, created_at)
                          VALUES (?, 'مرتجع', ?, ?, ?, ?, ?)''',
                       (product_id, qty, order['cost'] or 0, f"طلب رقم {order['id']}", 'مرتجع بعد التسليم', now_iso()))
        db.execute('UPDATE orders SET delivery_receivable=0, returned_at=? WHERE id=?', (now_iso(), order['id']))

    if old_status != 'مرتجع' and new_status == 'مرتجع' and old_status != 'تم التسليم':
        db.execute('UPDATE orders SET delivery_receivable=0, returned_at=? WHERE id=?', (now_iso(), order['id']))

    if old_status == 'مرتجع' and new_status == 'تم التسليم':
        if product_id:
            update_product_quantity(db, product_id, -qty)
            db.execute('''INSERT INTO inventory_movements (product_id, movement_type, quantity, unit_cost, reference, notes, created_at)
                          VALUES (?, 'إخراج', ?, ?, ?, ?, ?)''',
                       (product_id, qty, order['cost'] or 0, f"طلب رقم {order['id']}", 'تسليم بعد مرتجع', now_iso()))
        receivable = price if order['payment_method'] == 'شركة التوصيل' and delivery_company_id else 0
        db.execute('UPDATE orders SET delivery_receivable=?, delivered_at=? WHERE id=?', (receivable, now_iso(), order['id']))


@app.before_request
def ensure_db():
    init_db()


@app.route('/')
def dashboard():
    t = today_iso()
    stats = fetch_one('''
        SELECT COUNT(*) total_orders,
               COALESCE(SUM(price),0) total_sales,
               COALESCE(SUM(CASE WHEN status='تم التسليم' THEN price ELSE 0 END),0) delivered_sales,
               COALESCE(SUM(CASE WHEN status='مرتجع' THEN price ELSE 0 END),0) returns,
               COALESCE(SUM(CASE WHEN status='تم التسليم' THEN price-cost*quantity ELSE 0 END),0) profit
        FROM orders WHERE date(created_at)=?
    ''', (t,))
    by_status = fetch_all('SELECT status, COUNT(*) c FROM orders WHERE date(created_at)=? GROUP BY status', (t,))
    delivery_due = fetch_one('SELECT COALESCE(SUM(delivery_receivable-paid_to_lor),0) due FROM orders')['due']
    low_stock = fetch_all('SELECT * FROM products WHERE quantity <= 5 ORDER BY quantity ASC LIMIT 8')
    recent_orders = fetch_all('''SELECT o.*, d.name delivery_name, p.name product_name FROM orders o
                                 LEFT JOIN delivery_companies d ON d.id=o.delivery_company_id
                                 LEFT JOIN products p ON p.id=o.product_id
                                 ORDER BY o.id DESC LIMIT 8''')
    return render_template('dashboard.html', stats=stats, by_status=by_status, delivery_due=delivery_due, low_stock=low_stock, recent_orders=recent_orders)


@app.route('/orders/new', methods=['GET', 'POST'])
def new_order():
    products = fetch_all('SELECT * FROM products ORDER BY name')
    companies = fetch_all('SELECT * FROM delivery_companies ORDER BY name')
    if request.method == 'POST':
        product_id = request.form.get('product_id') or None
        quantity = int(request.form.get('quantity') or 1)
        price = float(request.form.get('price') or 0)
        cost = 0
        if product_id:
            p = fetch_one('SELECT * FROM products WHERE id=?', (product_id,))
            cost = float(p['cost'] or 0) if p else 0
        with get_db() as db:
            cur = db.execute('''INSERT INTO orders (customer_name, order_text, product_id, quantity, price, cost, status, payment_method,
                         delivery_company_id, notes, created_at, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (request.form['customer_name'], request.form['order_text'], product_id, quantity, price, cost,
                        request.form['status'], request.form['payment_method'], request.form.get('delivery_company_id') or None,
                        request.form.get('notes'), now_iso(), now_iso()))
            order_id = cur.lastrowid
            order = db.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
            apply_status_effect(db, order, 'جديد', request.form['status'])
            db.commit()
        flash('تمت إضافة الطلب بنجاح')
        return redirect(url_for('today_orders'))
    return render_template('order_form.html', statuses=ORDER_STATUSES, payments=PAYMENT_METHODS, products=products, companies=companies)


@app.route('/orders/today')
def today_orders():
    orders = fetch_all('''SELECT o.*, d.name delivery_name, p.name product_name FROM orders o
                          LEFT JOIN delivery_companies d ON d.id=o.delivery_company_id
                          LEFT JOIN products p ON p.id=o.product_id
                          WHERE date(o.created_at)=? ORDER BY o.id DESC''', (today_iso(),))
    return render_template('orders_today.html', orders=orders, statuses=ORDER_STATUSES)


@app.route('/orders')
def all_orders():
    status = request.args.get('status', '')
    q = request.args.get('q', '')
    params = []
    where = []
    if status:
        where.append('o.status=?'); params.append(status)
    if q:
        where.append('(o.customer_name LIKE ? OR o.order_text LIKE ?)'); params += [f'%{q}%', f'%{q}%']
    sql_where = 'WHERE ' + ' AND '.join(where) if where else ''
    orders = fetch_all(f'''SELECT o.*, d.name delivery_name, p.name product_name FROM orders o
                          LEFT JOIN delivery_companies d ON d.id=o.delivery_company_id
                          LEFT JOIN products p ON p.id=o.product_id
                          {sql_where} ORDER BY o.id DESC LIMIT 300''', params)
    return render_template('orders.html', orders=orders, statuses=ORDER_STATUSES, status=status, q=q)


@app.route('/orders/<int:order_id>/status', methods=['POST'])
def change_status(order_id):
    new_status = request.form['status']
    with get_db() as db:
        order = db.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
        if not order:
            flash('الطلب غير موجود')
            return redirect(url_for('today_orders'))
        old_status = order['status']
        apply_status_effect(db, order, old_status, new_status)
        db.execute('UPDATE orders SET status=?, updated_at=? WHERE id=?', (new_status, now_iso(), order_id))
        db.commit()
    flash('تم تحديث حالة الطلب')
    return redirect(request.referrer or url_for('today_orders'))


@app.route('/orders/<int:order_id>/payment', methods=['POST'])
def register_payment(order_id):
    amount = float(request.form.get('amount') or 0)
    with get_db() as db:
        db.execute('UPDATE orders SET paid_to_lor = paid_to_lor + ?, updated_at=? WHERE id=?', (amount, now_iso(), order_id))
        db.commit()
    flash('تم تسجيل التحصيل')
    return redirect(request.referrer or url_for('delivery'))


@app.route('/delivery', methods=['GET', 'POST'])
def delivery():
    if request.method == 'POST':
        with get_db() as db:
            db.execute('INSERT OR IGNORE INTO delivery_companies (name, phone, notes, created_at) VALUES (?, ?, ?, ?)',
                       (request.form['name'], request.form.get('phone'), request.form.get('notes'), now_iso()))
            db.commit()
        flash('تمت إضافة شركة التوصيل')
        return redirect(url_for('delivery'))
    companies = fetch_all('''SELECT d.*, COUNT(o.id) orders_count,
                             COALESCE(SUM(o.delivery_receivable),0) receivable,
                             COALESCE(SUM(o.paid_to_lor),0) paid,
                             COALESCE(SUM(o.delivery_receivable-o.paid_to_lor),0) due
                             FROM delivery_companies d
                             LEFT JOIN orders o ON o.delivery_company_id=d.id AND o.status='تم التسليم'
                             GROUP BY d.id ORDER BY d.name''')
    due_orders = fetch_all('''SELECT o.*, d.name delivery_name FROM orders o JOIN delivery_companies d ON d.id=o.delivery_company_id
                              WHERE o.status='تم التسليم' AND (o.delivery_receivable-o.paid_to_lor)>0
                              ORDER BY d.name, o.id DESC''')
    return render_template('delivery.html', companies=companies, due_orders=due_orders)


@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'POST':
        action = request.form.get('action')
        with get_db() as db:
            if action == 'product':
                db.execute('INSERT OR IGNORE INTO products (name, sku, cost, price, quantity, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                           (request.form['name'], request.form.get('sku'), float(request.form.get('cost') or 0),
                            float(request.form.get('price') or 0), int(request.form.get('quantity') or 0), now_iso()))
            elif action == 'movement':
                product_id = request.form['product_id']
                movement_type = request.form['movement_type']
                qty = int(request.form.get('quantity') or 0)
                delta = qty if movement_type in ['إدخال', 'مرتجع'] else -qty
                update_product_quantity(db, product_id, delta)
                db.execute('''INSERT INTO inventory_movements (product_id, movement_type, quantity, unit_cost, reference, notes, created_at)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (product_id, movement_type, qty, float(request.form.get('unit_cost') or 0), request.form.get('reference'), request.form.get('notes'), now_iso()))
            db.commit()
        flash('تم حفظ حركة المستودع')
        return redirect(url_for('inventory'))
    products = fetch_all('SELECT * FROM products ORDER BY name')
    movements = fetch_all('''SELECT m.*, p.name product_name FROM inventory_movements m JOIN products p ON p.id=m.product_id
                             ORDER BY m.id DESC LIMIT 50''')
    return render_template('inventory.html', products=products, movements=movements, movement_types=MOVEMENT_TYPES)


@app.route('/returns')
def returns():
    rows = fetch_all('''SELECT o.*, d.name delivery_name, p.name product_name FROM orders o
                        LEFT JOIN delivery_companies d ON d.id=o.delivery_company_id
                        LEFT JOIN products p ON p.id=o.product_id
                        WHERE o.status='مرتجع' ORDER BY o.returned_at DESC, o.id DESC''')
    return render_template('returns.html', rows=rows)


@app.route('/reports')
def reports():
    start = request.args.get('start') or today_iso()
    end = request.args.get('end') or today_iso()
    params = (start, end)
    summary = fetch_one('''SELECT COUNT(*) total_orders,
                           COALESCE(SUM(price),0) total_sales,
                           COALESCE(SUM(CASE WHEN status='تم التسليم' THEN price ELSE 0 END),0) delivered_sales,
                           COALESCE(SUM(CASE WHEN status='مرتجع' THEN price ELSE 0 END),0) returned_sales,
                           COALESCE(SUM(CASE WHEN status='تم التسليم' THEN price-cost*quantity ELSE 0 END),0) profit
                           FROM orders WHERE date(created_at) BETWEEN ? AND ?''', params)
    payments = fetch_all('''SELECT payment_method, COUNT(*) c, COALESCE(SUM(price),0) total
                            FROM orders WHERE date(created_at) BETWEEN ? AND ? GROUP BY payment_method''', params)
    statuses = fetch_all('''SELECT status, COUNT(*) c, COALESCE(SUM(price),0) total
                            FROM orders WHERE date(created_at) BETWEEN ? AND ? GROUP BY status''', params)
    movements = fetch_all('''SELECT movement_type, COUNT(*) c, COALESCE(SUM(quantity),0) qty
                             FROM inventory_movements WHERE date(created_at) BETWEEN ? AND ? GROUP BY movement_type''', params)
    return render_template('reports.html', start=start, end=end, summary=summary, payments=payments, statuses=statuses, movements=movements)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
