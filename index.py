import os
import json
import requests
import logging

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Получаем переменные окружения
BOT_TOKEN = os.environ['BOT_TOKEN']
YANDEX_API_KEY = os.environ['YANDEX_API_KEY']
FOLDER_ID = os.environ['FOLDER_ID']

YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Хранилище сессий
user_sessions = {}

def create_prompt(products):
    return f"""
Ты — опытный шеф-повар. Создай кулинарный рецепт используя эти продукты: {products}

Структура рецепта:
1. 🍽️ Название блюда
2. 📋 Ингредиенты с количествами
3. 👨‍🍳 Пошаговое приготовление (5 шагов)
4. ⏱️ Время готовки
5. 💡 Полезный совет

Рецепт должен быть реалистичным и простым для приготовления. Язык: русский.
"""

def get_recipe_from_yagpt(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "x-folder-id": FOLDER_ID
    }
    
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "user",
                "text": prompt
            }
        ]
    }
    
    response = requests.post(YANDEX_GPT_URL, headers=headers, json=data, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Ошибка YandexGPT: {response.status_code}")
    
    result = response.json()
    return result['result']['alternatives'][0]['message']['text']

def send_telegram_message(chat_id, text, parse_mode=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if parse_mode:
        data["parse_mode"] = parse_mode
    
    requests.post(url, json=data)

def handler(event, context):
    """Основная функция-обработчик для Yandex Cloud Functions"""
    try:
        # Парсим входящее сообщение от Telegram
        update = json.loads(event['body'])
        message = update.get('message', {})
        chat_id = str(message['chat']['id'])
        text = message.get('text', '').strip()
        
        logger.info(f"Получено сообщение: {text} от {chat_id}")
        
        # Обработка команды /start
        if text == '/start':
            welcome_text = """
🍳 *Привет! Я RecipeChefAI - твой помощник в готовке!*

Просто отправь мне список продуктов через запятую, и я придумаю вкусный рецепт!

*Например:* курица, рис, лук, морковь, помидоры

*Готов готовить? Отправляй продукты!* 🚀
            """
            send_telegram_message(chat_id, welcome_text, "Markdown")
            user_sessions[chat_id] = {"step": "awaiting_products"}
            
        # Обработка списка продуктов
        elif user_sessions.get(chat_id, {}).get('step') == 'awaiting_products' and text:
            send_telegram_message(chat_id, "🎯 *Генерирую рецепт...*", "Markdown")
            
            try:
                prompt = create_prompt(text)
                recipe_text = get_recipe_from_yagpt(prompt)
                send_telegram_message(chat_id, recipe_text)
                
                # Завершаем сессию
                del user_sessions[chat_id]
                
            except Exception as e:
                logger.error(f"Ошибка генерации: {str(e)}")
                send_telegram_message(chat_id, "❌ Произошла ошибка. Попробуйте еще раз.")
                del user_sessions[chat_id]
                
        # Неизвестная команда
        else:
            send_telegram_message(chat_id, "Начни с команды /start")
        
        return {
            'statusCode': 200,
            'body': 'OK'
        }
        
    except Exception as e:
        logger.error(f"Ошибка в handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }
