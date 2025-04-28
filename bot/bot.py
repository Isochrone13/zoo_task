# bot.py

import os
import sys
import logging
import json
from telegram.ext import (
    ApplicationBuilder,      # Класс для сборки и запуска приложения
    CommandHandler,          # Обработчик «команд» (/start и т. д.)
    CallbackQueryHandler,    # Обработчик нажатий inline-кнопок
    MessageHandler,          # Обработчик простых текстовых сообщений
    filters                  # Утилиты для фильтрации апдейтов
)
import handlers              # Модуль с бизнес-логикой и хэндлерами

# 1. Определяем константы
BOT_TOKEN = os.getenv("BOT_TOKEN", "7553793746:AAGggx0uIdPFKXoZMEvFVdlLRjLrouLRpyc")  # токен бота
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID", "442103705"))                 # id чата поддержки

BASE_DIR = os.path.dirname(os.path.abspath(__file__))                                 # строим абсолютные пути к папкам проекта
DATA_DIR = os.path.join(BASE_DIR, "..", "data")                                       # путь к папке с данными
MEDIA_DIR = os.path.join(BASE_DIR, "..", "media", "images")                           # путь к папкам с картинками

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
ANIMALS = load_json("animals.json")                                                   # читает JSON-файл с животными
QUIZ    = load_json("quiz.json")                                                      # читает JSON-файлы с викториной

# 2. Определяем метод load_json() 


# 3. Сохраняем логи в файл bot.log, и выводим в консоль.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 4. Передаем глобальные данные в модуль handlers, где описаны функции-обработчики
handlers.ANIMALS = ANIMALS
handlers.QUIZ = QUIZ
handlers.MEDIA_DIR = MEDIA_DIR

# 5. Создаём приложение и сразу регистрируем хэндлеры в нужном порядке 
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Основные хэндлеры
    app.add_handler(CommandHandler("start", handlers.start), group=0)                           # логотип + меню
    app.add_handler(CallbackQueryHandler(handlers.start_quiz, pattern="^start_quiz$"), group=0) # инициализирует счётчики + первый вопрос
    app.add_handler(CallbackQueryHandler(handlers.answer_handler, pattern=r"^ans\|"), group=0)  # записывает вес ответа, идёт к следующему
    # «Связь», «Попробовать снова», «Отзыв»
    app.add_handler(CallbackQueryHandler(handlers.button_handler, pattern="^(contact|restart|feedback)$"), group=0)
    # Reply-кнопки («Викторина», «Отзыв», «Связь», «Помощь») + текстовые ответы
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.message_handler), group=0)

    # Логирование всех обновлений
    app.add_handler(MessageHandler(filters.ALL, handlers.log_update), group=1)
    app.add_handler(CallbackQueryHandler(handlers.log_update), group=1)

    # Обработка ошибок
    app.add_error_handler(handlers.error_handler)

# ловим необработанные исключения и запускаем long-polling
    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
