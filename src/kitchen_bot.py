import sqlite3
from enum import Enum
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify


app = Flask(__name__)

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

# مثالين للتأكد من تشغيل الكود
def example():
    create_tables()  # إنشاء الجداول
    add_menu_items()  # إضافة الوجبات
    
# قم بتشغيل المثال إذا تم استيراد الملف كبرنامج رئيسي
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # تشغيل على المنفذ 5001
    app.run(host='0.0.0.0', port=port)
