import sqlite3
import threading


lock = threading.Lock()
connection = None
cursor = None


def open_connection(pathname):
    global connection, cursor
    if connection is None:
        connection = sqlite3.connect(pathname, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS product_names("
                       "product_id INTEGER PRIMARY KEY, "
                       "product_name TEXT NOT NULL, "
                       "walmart_sku TEXT NOT NULL, "
                       "amazon_asin TEXT NOT NULL, "
                       "walmart_price REAL DEFAULT -1.0 NOT NULL, "
                       "amazon_price REAL DEFAULT -1.0 NOT NULL, "
                       "CONSTRAINT product_name_unique UNIQUE(product_name));")
        connection.commit()


def close_connection():
    global connection, cursor
    if connection is not None:
        connection.close()
        connection = None
        cursor = None


def get_product_id(product_name):
    lock.acquire()
    cursor.execute("SELECT product_id FROM product_names WHERE product_name=?;", (product_name,))
    result = cursor.fetchone()
    lock.release()
    if result is not None:
        result = result[0]
    return result


def get_product_ids(product_names):
    product_ids = len(product_names) * [None]
    lock.acquire()
    cursor.execute(
        "SELECT product_id, product_name FROM product_names WHERE product_name in(" +
        ",".join(['?' for _ in product_names]) + ");",
        tuple(product_names))
    result = cursor.fetchall()
    lock.release()
    for (product_id, product_name) in result:
        product_ids[product_names.index(product_name)] = product_id
    return product_ids


def get_product(product_id):
    lock.acquire()
    cursor.execute("SELECT * FROM product_names WHERE product_id=?;", (product_id,))
    result = cursor.fetchone()
    lock.release()
    return list(result)


def get_products(product_ids):
    products = len(product_ids) * [None]
    lock.acquire()
    cursor.execute(
        "SELECT * FROM product_names WHERE product_id in(" + ",".join(['?' for _ in product_ids]) + ");",
        tuple(product_ids))
    results = cursor.fetchall()
    lock.release()
    for result in results:
        product_id = result[0]
        idx = product_ids.index(product_id)
        products[idx] = list(result)
    return products


def insert_product(product_name, walmart_sku, amazon_asin):
    """
    Throws sqlite3.IntegrityError if product_name is already in the database.
    """
    lock.acquire()
    cursor.execute("INSERT INTO product_names(product_name, walmart_sku, amazon_asin) VALUES(?,?,?);",
                   (product_name, walmart_sku, amazon_asin))
    result = cursor.lastrowid
    connection.commit()
    lock.release()
    return result


def delete_product(product_id):
    lock.acquire()
    cursor.execute("DELETE FROM product_names WHERE product_id=?;", (product_id,))
    connection.commit()
    lock.release()


def rename_product_name(old_product_name, new_product_name):
    lock.acquire()
    cursor.execute("UPDATE product_names SET product_name=? WHERE product_name=?;",
                   (new_product_name, old_product_name))
    connection.commit()
    lock.release()


def set_product_prices(product_id, walmart_price, amazon_price):
    lock.acquire()
    cursor.execute("UPDATE product_names SET walmart_price=?, amazon_price=? WHERE product_id=?;",
                   (walmart_price, amazon_price, product_id))
    connection.commit()
    lock.release()


def print_all():  # Debug
    lock.acquire()
    rows = cursor.execute("SELECT * FROM product_names;")
    lock.release()
    for row in rows:
        print(row)
