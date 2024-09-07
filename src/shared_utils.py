import sqlite3
from enum import Enum
import os

# رابط 
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

# حالات الطلب
class OrderStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    READY = "ready"
    DELIVERED = "delivered"

# اتصال بقاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('restaurant.db')
    conn.row_factory = sqlite3.Row
    return conn

# إنشاء جداول قاعدة البيانات
def create_tables():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS menu
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY, user_id INTEGER, status TEXT, phone_number TEXT, location_lat REAL, location_lon REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS order_items
                 (id INTEGER PRIMARY KEY, order_id INTEGER, menu_item_id INTEGER, quantity INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kitchen_chats
                 (id INTEGER PRIMARY KEY, chat_id TEXT)''')
    conn.commit()
    conn.close()

# إضافة بعض الوجبات إلى قاعدة البيانات
def add_menu_items():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM menu")  # للتأكد من أن القائمة تكون محدثة
    menu_items = [
        ('بيتزا', 10.99, 'بيتزا لذيذة بالجبن'),
        ('برغر', 7.99, 'برغر لحم طازج'),
        ('باستا', 8.99, 'باستا كريمية ألفريدو'),
        ('سوشي', 12.99, 'سوشي سلمون طازج'),
        ('سلطة', 6.99, 'سلطة خضراء صحية')
    ]
    c.executemany("INSERT INTO menu (name, price, description) VALUES (?, ?, ?)", menu_items)
    conn.commit()
    conn.close()