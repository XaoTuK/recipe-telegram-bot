import os
import logging
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Детальная настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

class YandexGPTDebug:
    def __init__(self):
        # Используем ПРАВИЛЬНЫЙ folder_id из ошибки
        self.api_key = "AQVN2ISkHPTzTQ7PRtnMP5pVWr17W-hEv0WNqn8c"
        self.folder_id = "b1gne1sf06u2lnsieuk9"  # 👈 ЗАМЕНИЛИ НА ПРАВИЛЬНЫЙ!
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        logger.info(f"API Key: {self.api_key[:10]}...")
        logger.info(f"Folder ID: {self.folder_id}")  # 👈 Теперь правильный!
    
    def test_connection(self):
        """Тестирует базовое соединение с Яндекс API"""
        test_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/models"
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info("🔍 Тестируем соединение с Яндекс API...")
            response = requests.get(test_url, headers=headers, timeout=10)
            
            logger.info(f"📡 Статус тестового запроса: {response.status_code}")
            
            if response.status_code == 200:
                return "✅ Соединение с Яндекс API установлено!"
            else:
                return f"❌ Ошибка соединения: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"❌ Исключение при тесте: {str(e)}"
    
    def make_request(self, messages):
        """Отправляет запрос к Yandex GPT API"""
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",  # 👈 Теперь правильный folder_id!
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 2000
            },
            "messages": messages
        }
        
        try:
            logger.info("🔄 Отправляем запрос к Яндекс GPT...")
            response = requests.post(
                self.base_url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"📡 HTTP статус: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Успешный ответ от Яндекс GPT!")
                return result['result']['alternatives'][0]['message']['text']
            else:
                error_msg = f"❌ Ошибка API: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"💥 Ошибка: {str(e)}"
            logger.error(error_msg)
            return error_msg

# Инициализация Яндекс GPT
yandex_gpt = YandexGPTDebug()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
👨‍🍳 Привет! Я бот-шеф!

Команды:
/start - начать работу
/test - проверить соединение с Яндекс API

Просто напиши, что хочешь приготовить!
"""
    await update.message.reply_text(welcome_text)

async def test_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка соединения с Яндекс API"""
    await update.message.reply_text("🔍 Проверяем соединение с Яндекс API...")
    test_result = yandex_gpt.test_connection()
    await update.message.reply_text(test_result)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="typing"
    )
    
    messages = [
        {
            "role": "system",
            "text": "Ты профессиональный шеф-повар. Давай подробные рецепты с ингредиентами и пошаговыми инструкциями. Будь креативным и полезным."
        },
        {
            "role": "user", 
            "text": user_message
        }
    ]
    
    response_text = yandex_gpt.make_request(messages)
    await update.message.reply_text(response_text)

def main():
    telegram_token = "8462003240:AAEzP4drh3jb6FErp26qr_HaRMjQF9i1OII"
    
    logger.info("🚀 Запускаем бота с исправленным folder_id...")
    
    application = Application.builder().token(telegram_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_connection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Бот запущен с правильным folder_id!")
    application.run_polling()

if __name__ == '__main__':
    main()
