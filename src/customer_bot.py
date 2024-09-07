import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters
from src.shared_utils import NGROK_URL, OrderStatus, get_db_connection, create_tables, add_menu_items
import sqlite3
import requests
from flask import Flask, request, jsonify
from enum import Enum
import asyncio
import os
# تكوين السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# حالات المحادثة
MENU, ORDERING, CONFIRM_ORDER, SELECT_QUANTITY, CONTACT_INFO = range(5)

# حالات الطلب
class OrderStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    READY = "ready"
    DELIVERED = "delivered"

# توكن البوت
CUSTOMER_BOT_TOKEN = "7204756264:AAELkwGBuumSl42cQxtXZWbXKIUCtSEmIuw"

# رابط ngrok

# إعداد Flask للـ Webhook و API
app = Flask(__name__)

# إعداد التطبيق
customer_application = Application.builder().token(CUSTOMER_BOT_TOKEN).build()

# اتصال بقاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('restaurant.db')
    conn.row_factory = sqlite3.Row
    return conn

# وظائف API
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO orders (user_id, status) VALUES (?, ?)', (data['user_id'], OrderStatus.PENDING.value))
    order_id = c.lastrowid
    for item in data['items']:
        c.execute('INSERT INTO order_items (order_id, menu_item_id, quantity) VALUES (?, ?, ?)', 
                  (order_id, item['menu_item_id'], item['quantity']))
    conn.commit()
    conn.close()
    return jsonify({"order_id": order_id}), 201

# وظائف البوت الأساسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("عرض القائمة", callback_data='menu')],
        [InlineKeyboardButton("طلب جديد", callback_data='new_order')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('مرحبًا بك في مطعمنا! كيف يمكنني مساعدتك؟', reply_markup=reply_markup)
    return MENU

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM menu').fetchall()
    conn.close()
    
    keyboard = [[InlineKeyboardButton(f"{item['name']} - {item['price']}$", callback_data=f'order_{item["id"]}')] for item in menu_items]
    keyboard.append([InlineKeyboardButton("العودة", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text="اختر من القائمة:", reply_markup=reply_markup)
    return ORDERING

async def add_to_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split('_')[1])
    if 'cart' not in context.user_data:
        context.user_data['cart'] = []
    context.user_data['cart'].append(item_id)
    
    keyboard = [
        [InlineKeyboardButton("مواصلة التسوق", callback_data='continue_shopping')],
        [InlineKeyboardButton("إنهاء الطلب", callback_data='finish_order')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text="تمت إضافة العنصر إلى السلة. ماذا تريد أن تفعل الآن؟", reply_markup=reply_markup)
    return ORDERING

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if 'cart' not in context.user_data or not context.user_data['cart']:
        await query.edit_message_text(text="سلة التسوق فارغة. يرجى إضافة بعض العناصر أولاً.")
        return MENU
    
    order_items = []
    for item_id in context.user_data['cart']:
        order_items.append({"menu_item_id": item_id, "quantity": 1})
    
    response = requests.post(f"{NGROK_URL}/api/orders", json={
        "user_id": update.effective_user.id,
        "items": order_items
    })
    
    if response.status_code == 201:
        order_id = response.json()['order_id']
        await query.edit_message_text(text=f"تم إنشاء طلبك برقم {order_id}. سنتواصل معك قريبًا لتأكيد الطلب.")
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await query.edit_message_text(text="عذرًا، حدث خطأ أثناء إنشاء طلبك. يرجى المحاولة مرة أخرى لاحقًا.")
        return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('تم إلغاء العملية. هل تريد شيئًا آخر؟')
    return ConversationHandler.END

def setup_customer_bot():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [CallbackQueryHandler(menu, pattern='^menu$'),
                   CallbackQueryHandler(start, pattern='^new_order$')],
            ORDERING: [CallbackQueryHandler(add_to_order, pattern='^order_'),
                       CallbackQueryHandler(menu, pattern='^continue_shopping$'),
                       CallbackQueryHandler(finish_order, pattern='^finish_order$')],
            CONTACT_INFO: [MessageHandler(filters.CONTACT | filters.LOCATION, lambda u, c: None)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    customer_application.add_handler(conv_handler)

@app.route(f'/{CUSTOMER_BOT_TOKEN}', methods=['POST'])
def customer_webhook():
    update = Update.de_json(request.get_json(), customer_application.bot)
    customer_application.process_update(update)
    return 'OK'

async def main():
    setup_customer_bot()
    await customer_application.bot.set_webhook(f"{NGROK_URL}/{CUSTOMER_BOT_TOKEN}")
    app.run(port=5000)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)