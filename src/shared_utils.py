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
            menu_item_id INTEGER,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (menu_item_id) REFERENCES menu(id)
        )
    ''')
    
    # إنشاء جدول محادثات المطبخ
    c.execute('''
        CREATE TABLE IF NOT EXISTS kitchen_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL UNIQUE
        )
    ''')
    
    conn.commit()
    conn.close()

# إضافة بعض الوجبات إلى قاعدة البيانات
def add_menu_items():
    conn = get_db_connection()
    c = conn.cursor()
    
    # التأكد من أن القائمة تكون محدثة
    c.execute("DELETE FROM menu")
    
    # إضافة الوجبات إلى جدول القائمة
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

# الحصول على جميع محادثات المطبخ
def get_kitchen_chats():
    conn = get_db_connection()
    c = conn.cursor()
    chats = c.execute('SELECT chat_id FROM kitchen_chats').fetchall()
    conn.close()
    return [chat['chat_id'] for chat in chats]

# تحديث حالة الطلب
def update_order_status(order_id, new_status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()

# الحصول على تفاصيل الطلب
def get_order_details(order_id):
    conn = get_db_connection()
    c = conn.cursor()
    order = c.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if order:
        items = c.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,)).fetchall()
        order_dict = dict(order)
        order_dict['items'] = [dict(item) for item in items]
        conn.close()
        return order_dict
    conn.close()
    return None

# إضافة محادثة مطبخ جديدة
def add_kitchen_chat(chat_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO kitchen_chats (chat_id) VALUES (?)', (chat_id,))
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات
def initialize_database():
    create_tables()
    add_menu_items()

# يمكن إضافة المزيد من الوظائف المساعدة هنا حسب الحاجة