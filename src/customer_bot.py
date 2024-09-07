import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from shared_utils import BASE_URL, OrderStatus, get_db_connection, create_tables
import sqlite3
import requests
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# تكوين السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# توكن البوت
KITCHEN_BOT_TOKEN = os.getenv('KITCHEN_BOT_TOKEN')

# إعداد Flask للـ Webhook و API
app = Flask(__name__)

# إعداد التطبيق
kitchen_application = Application.builder().token(KITCHEN_BOT_TOKEN).build()

# وظائف API
@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    conn = get_db_connection()
    c = conn.cursor()
    order = c.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if order:
        items = c.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,)).fetchall()
        order_dict = dict(order)
        order_dict['items'] = [dict(item) for item in items]
        conn.close()
        return jsonify(order_dict), 200
    conn.close()
    return jsonify({"error": "Order not found"}), 404

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ? WHERE id = ?', (data['status'], order_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Order updated successfully"}), 200

# وظائف البوت
async def handle_kitchen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    action, order_id = query.data.split('_')
    order_id = int(order_id)
    
    if action == 'accept':
        new_status = OrderStatus.ACCEPTED.value
    elif action == 'ready':
        new_status = OrderStatus.READY.value
    else:
        await query.edit_message_text(text="إجراء غير صالح.")
        return
    
    response = requests.put(f"{BASE_URL}/api/orders/{order_id}", json={"status": new_status})
    
    if response.status_code == 200:
        await query.edit_message_text(text=f"تم تحديث حالة الطلب رقم {order_id} إلى {new_status}.")
        # إرسال إشعار للزبون (يمكن تنفيذه عبر API منفصل)
    else:
        await query.edit_message_text(text="عذرًا، حدث خطأ أثناء تحديث حالة الطلب.")

async def register_kitchen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO kitchen_chats (chat_id) VALUES (?)', (chat_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("تم تسجيل هذه الدردشة كدردشة مطبخ بنجاح.")

def setup_kitchen_bot():
    kitchen_application.add_handler(CallbackQueryHandler(handle_kitchen, pattern='^(accept|ready)_'))
    kitchen_application.add_handler(CommandHandler('register', register_kitchen))

@app.route(f'/{KITCHEN_BOT_TOKEN}', methods=['POST'])
def kitchen_webhook():
    update = Update.de_json(request.get_json(), kitchen_application.bot)
    kitchen_application.process_update(update)
    return 'OK'

async def main():
    setup_kitchen_bot()
    await kitchen_application.bot.set_webhook(f"{BASE_URL}/{KITCHEN_BOT_TOKEN}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # استخدام منفذ مختلف عن بوت الزبائن
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', port, app)