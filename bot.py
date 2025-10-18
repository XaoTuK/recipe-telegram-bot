import os
import logging
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Состояния диалога
PRODUCTS, MEAL_TYPE = range(2)

class YandexGPT:
    def __init__(self):
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        logger.info(f"API Key: {self.api_key[:10]}...")
        logger.info(f"Folder ID: {self.folder_id}")
        
        if not self.api_key:
            logger.error("❌ YANDEX_API_KEY не найден!")
        if not self.folder_id:
            logger.error("❌ YANDEX_FOLDER_ID не найден!")
        
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
        
        logger.info(f"🔄 Отправляем запрос к Яндекс GPT...")
        logger.info(f"📝 Продукты: {products}")
        logger.info(f"📝 Прием пищи: {meal_type}")
        logger.info(f"📝 Данные: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = requests.post(
                self.base_url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"📡 HTTP статус: {response.status_code}")
            logger.info(f"📡 Текст ответа: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Успешный ответ от Яндекс GPT!")
                return result['result']['alternatives'][0]['message']['text']
            else:
                error_msg = f"❌ Ошибка API: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "⏰ Таймаут запроса к API"
            logger.error(error_msg)
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "🔌 Ошибка подключения к API"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"💥 Неожиданная ошибка: {str(e)}"
            logger.error(error_msg)
            return error_msg

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
    
    logger.info(f"📥 Получены продукты: {products}")
    
    await update.message.reply_text(
        "🍽️ Отлично! Какой это прием пищи?\n"
        "• завтрак\n• обед\n• ужин\n• перекус"
    )
    return MEAL_TYPE

async def receive_meal_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meal_type = update.message.text.lower()
    products = context.user_data['products']
    
    logger.info(f"📥 Получен прием пищи: {meal_type}")
    
    await update.message.reply_text("👨‍🍳 Придумываю рецепт...")
    
    response_text = yandex_gpt.make_request(products, meal_type)
    await update.message.reply_text(response_text)
    
    # Сбрасываем состояние для нового запроса
    return PRODUCTS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("До свидания!")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"💥 Ошибка в боте: {context.error}")
    if update and update.message:
        await update.message.reply_text(f"❌ Ошибка бота: {context.error}")

def main():
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    
    if not telegram_token:
        logger.error("❌ TELEGRAM_TOKEN не найден!")
        return
    
    logger.info("🚀 Запускаем бота с отладкой...")
    
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
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
