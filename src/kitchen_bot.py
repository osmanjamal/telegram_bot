import sqlite3
from enum import Enum
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# رابط BASE_URL من المتغيرات البيئية
BASE_URL = os.getenv('BASE_URL', 'https://telegram-bot-2dhn.onrender.com')

# حالات الطلب
class OrderStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    READY = "ready"
    DELIVERED = "delivered"

# الاتصال بقاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('restaurant.db')
    conn.row_factory = sqlite3.Row
    return conn

# إنشاء جداول قاعدة البيانات
def create_tables():
    conn = get_db_connection()
    c = conn.cursor()
    
    # إنشاء جدول القوائم
    c.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    ''')
    
    # إنشاء جدول الطلبات
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            phone_number TEXT,
            location_lat REAL,
            location_lon REAL
        )
    ''')
    
    # إنشاء جدول عناصر الطلبات
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            menu_