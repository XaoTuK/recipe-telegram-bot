import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
PRODUCTS, MEAL_TYPE = range(2)

class YandexGPT:
    def __init__(self):
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
    def make_request(self, products, meal_type):
        messages = [
            {
                "role": "system", 
                "text": f"""Ты шеф-повар. Создай рецепт для {meal_type} используя эти продукты: {products}.
                
Формат:
🍽️ [Название блюда] - {meal_type}
📋 Ингредиенты (точные пропорции)
👨‍🍳 Пошаговое приготовление
💡 Полезный совет

Будь креативным, используй эмодзи, дай точные количества."""
            },
            {
                "role": "user", 
                "text": f"Продукты: {products}, Прием пищи: {meal_type}"
            }
        ]
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 1500
            },
            "messages": messages
        }
        
        try:
            response = requests.post(self.base_url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['result']['alternatives'][0]['message']['text']
            else:
                return f"❌ Ошибка API: {response.status_code}"
                
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"

yandex_gpt = YandexGPT()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👨‍🍳 Привет! Я бот-шеф!\n\n"
        "Напиши продукты которые у тебя есть, и я предложу рецепт!"
    )
    return PRODUCTS

async def receive_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = update.message.text
    context.user_data['products'] = products
    
    await update.message.reply_text(
        "🍽️ Отлично! Какой это прием пищи?\n"
        "• завтрак\n• обед\n• ужин\n• перекус"
    )
    return MEAL_TYPE

async def receive_meal_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meal_type = update.message.text.lower()
    products = context.user_data['products']
    
    await update.message.reply_text("👨‍🍳 Придумываю рецепт...")
    
    response_text = yandex_gpt.make_request(products, meal_type)
    await update.message.reply_text(response_text)
    
    return PRODUCTS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("До свидания!")
    return ConversationHandler.END

def main():
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    
    application = Application.builder().token(telegram_token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_products)],
            MEAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_meal_type)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
