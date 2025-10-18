import os
import logging
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Детальная настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Изменили на DEBUG для максимальной информации
)
logger = logging.getLogger(__name__)

class YandexGPTDebug:
    def __init__(self):
        # Для отладки используем прямые значения
        self.api_key = "AQVN2ISkHPTzTQ7PRtnMP5pVWr17W-hEv0WNqn8c"
        self.folder_id = "b1g8k14p2bqfrf2djq0c"
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        logger.info(f"API Key: {self.api_key[:10]}...")  # Логируем только начало ключа
        logger.info(f"Folder ID: {self.folder_id}")
        logger.info(f"Base URL: {self.base_url}")
    
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
            logger.info(f"📡 Заголовки ответа: {dict(response.headers)}")
            
            if response.status_code == 200:
                return "✅ Соединение с Яндекс API установлено"
            else:
                return f"❌ Ошибка соединения: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"❌ Исключение при тесте: {str(e)}"
    
    def make_request(self, messages):
        """Отправляет запрос к Yandex GPT API с детальной отладкой"""
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TelegramChefBot/1.0"
        }
        
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 2000
            },
            "messages": messages
        }
        
        # Логируем детали запроса
        logger.info("🔄 Отправляем запрос к Яндекс GPT...")
        logger.info(f"📝 URL: {self.base_url}")
        logger.info(f"📝 Заголовки: {headers}")
        logger.info(f"📝 Данные: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = requests.post(
                self.base_url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            # Детальное логирование ответа
            logger.info(f"📡 HTTP статус: {response.status_code}")
            logger.info(f"📡 Заголовки ответа: {dict(response.headers)}")
            logger.info(f"📡 Текст ответа: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Успешный ответ от Яндекс GPT")
                return result['result']['alternatives'][0]['message']['text']
            
            elif response.status_code == 401:
                error_msg = "❌ Ошибка 401: Неавторизован. Проверьте API ключ и Folder ID"
                logger.error(error_msg)
                return error_msg
                
            elif response.status_code == 403:
                error_msg = "❌ Ошибка 403: Доступ запрещен. Проверьте права доступа"
                logger.error(error_msg)
                return error_msg
                
            elif response.status_code == 404:
                error_msg = "❌ Ошибка 404: Ресурс не найден. Проверьте URL и модель"
                logger.error(error_msg)
                return error_msg
                
            elif response.status_code == 429:
                error_msg = "❌ Ошибка 429: Слишком много запросов. Лимит превышен"
                logger.error(error_msg)
                return error_msg
                
            elif response.status_code == 500:
                error_msg = "❌ Ошибка 500: Внутренняя ошибка сервера Яндекс"
                logger.error(error_msg)
                return error_msg
                
            else:
                error_msg = f"❌ Ошибка API: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "⏰ Таймаут запроса к API (30 сек)"
            logger.error(error_msg)
            return error_msg
            
        except requests.exceptions.ConnectionError:
            error_msg = "🔌 Ошибка подключения к Яндекс API"
            logger.error(error_msg)
            return error_msg
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"🌐 HTTP ошибка: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"💥 Неожиданная ошибка: {str(e)}"
            logger.error(error_msg)
            return error_msg

# Инициализация Яндекс GPT
yandex_gpt = YandexGPTDebug()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
👨‍🍳 Привет! Я бот-шеф с отладкой!

Команды:
/start - начать работу
/test - проверить соединение с Яндекс API
/debug - полная диагностика

Просто напиши, что хочешь приготовить!
"""
    await update.message.reply_text(welcome_text)

async def test_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка соединения с Яндекс API"""
    await update.message.reply_text("🔍 Проверяем соединение с Яндекс API...")
    
    test_result = yandex_gpt.test_connection()
    await update.message.reply_text(test_result)

async def debug_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Полная диагностика"""
    debug_text = f"""
🔧 ДИАГНОСТИКА БОТА:

📡 API ключ: {yandex_gpt.api_key[:10]}...
📁 Folder ID: {yandex_gpt.folder_id}
🌐 Endpoint: {yandex_gpt.base_url}

Используйте /test для проверки соединения
"""
    await update.message.reply_text(debug_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    
    # Показываем индикатор набора
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="typing"
    )
    
    # Формируем сообщения для GPT
    messages = [
        {
            "role": "system",
            "text": "Ты профессиональный шеф-повар. Давай подробные рецепты."
        },
        {
            "role": "user", 
            "text": user_message
        }
    ]
    
    # Получаем ответ от Яндекс GPT
    response_text = yandex_gpt.make_request(messages)
    
    # Добавляем отладочную информацию
    debug_info = f"""
💬 Ваш запрос: {user_message}
📡 Ответ API: {response_text[:100]}...
"""
    logger.info(debug_info)
    
    # Отправляем ответ пользователю
    await update.message.reply_text(response_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"💥 Ошибка в боте: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(f"❌ Ошибка бота: {context.error}")

def main():
    """Основная функция запуска бота"""
    telegram_token = "8462003240:AAEzP4drh3jb6FErp26qr_HaRMjQF9i1OII"
    
    logger.info("🚀 Запускаем бота с отладкой...")
    
    # Создаем приложение
    application = Application.builder().token(telegram_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_connection))
    application.add_handler(CommandHandler("debug", debug_info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("✅ Бот запущен и готов к работе")
    application.run_polling()
    logger.info("❌ Бот остановлен")

if __name__ == '__main__':
    main()
