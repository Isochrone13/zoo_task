import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import ContextTypes

# Глобальные переменные. Их подставляет bot.py перед стартом:
ANIMALS = {}             # словарь профилей животных из animals.json
QUIZ = []                # список вопросов викторины из quiz.json
MEDIA_DIR = ""           # путь к папке с изображениями

# Имя файла-логотипа зоопарка, лежит в MEDIA_DIR
LOGO_FILENAME = "moscow_zoo.png"

# Клавиатура, которая всегда выводится под полем ввода (Reply Keyboard)
MAIN_KEYBOARD = [
    ["🧩 Викторина", "📝 Отзыв"],
    ["✉️ Связь",   "ℹ️ Помощь"],
]

def get_main_kb():
    """
    Возвращает объект ReplyKeyboardMarkup,
    чтобы кнопки не исчезали после нажатия.
    """
    return ReplyKeyboardMarkup(
        MAIN_KEYBOARD,
        resize_keyboard=True,
        one_time_keyboard=False
    )

# Логирование входящих соообщений
async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если это обычное сообщение
    if update.message:
        text = update.message.text or '<non-text>'
        user = update.effective_user
        print(f"MSG from {user.id}: {text}")
    # Если это нажатие inline-кнопки
    elif update.callback_query:
        cq = update.callback_query
        print(f"CBQ from {cq.from_user.id}: {cq.data}")

# Обработчик всех необработанных ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error handling update {update}: {context.error}")

# Основные хэндлеры

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start — сначала отправляем логотип зоопарка (если он есть),
    затем приветственный текст и показываем MAIN_KEYBOARD.
    """
    logo_path = os.path.join(MEDIA_DIR, LOGO_FILENAME)
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as logo:
            await update.message.reply_photo(photo=logo)

    text = (
        "Приветствуем!\n\n"
        "Вы попали в место, где вам помогут взять животное под опеку!\n\n"
        "Участие в программе «Клуб друзей зоопарка» — это помощь в содержании наших обитателей, "
        "а также ваш личный вклад в дело сохранения биоразнообразия Земли и развитие нашего зоопарка.\n\n"
        "Чтобы определиться с животным, пройдите небольшую викторину «Какое у вас тотемное животное?»\n\n"
    )
    await update.message.reply_text(text, reply_markup=get_main_kb())

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Инициализирует данные викторины:
     - Сбрасывает пользовательские данные
     - Устанавливает счетчики scores и индекс вопроса q_index
     - Запускает первый вопрос через ask_question()
    Позволяет вызывать как из /start (message), так и из inline-кнопки.
    """
    if update.callback_query:
        cq = update.callback_query
        await cq.answer()           # отвечаем «тихо», чтобы кнопка снялась
        update_or_query = cq
    else:
        update_or_query = update

    # Сбрасываем всё в context.user_data
    context.user_data.clear()
    context.user_data['scores'] = {k: 0 for k in ANIMALS}
    context.user_data['q_index'] = 0

    await ask_question(update_or_query, context)

async def ask_question(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """
    Берет следующий вопрос по индексу q_index из context.user_data.
    Если вопросы еще остались — отправляет текст + inline-кнопки с вариантами,
    иначе — вызывает show_result().
    """
    q_idx = context.user_data.get('q_index', 0)
    if q_idx < len(QUIZ):
        q = QUIZ[q_idx]
        buttons = [
            [InlineKeyboardButton(ans['text'], callback_data=f"ans|{i}")]
            for i, ans in enumerate(q['answers'])
        ]
        # Выбираем правильный метод отправки в зависимости от типа update
        sender = (
            update_or_query.message.reply_text
            if hasattr(update_or_query, 'message')
            else update_or_query.edit_message_text
        )
        await sender(q['question'], reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await show_result(update_or_query, context)

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие на вариант ответа (callback_data вида "ans|<idx>"):
     - Разбирает индекс ответа
     - Добавляет веса к счетчикам в context.user_data['scores']
     - Увеличивает q_index и вызывает ask_question() для следующего
    """
    cq = update.callback_query
    await cq.answer()

    _, idx_str = cq.data.split('|')
    idx = int(idx_str)
    q_idx = context.user_data.get('q_index', 0)

    # Прибавляем веса
    for key in QUIZ[q_idx]['answers'][idx].get('weights', []):
        if key in context.user_data['scores']:
            context.user_data['scores'][key] += 1

    # Переходим к следующему вопросу
    context.user_data['q_index'] = q_idx + 1
    await ask_question(cq, context)

async def show_result(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """
    По завершении викторины:
     - Находит максимальный счетчик в scores → победитель
     - Загружает профиль из ANIMALS[winner]
     - Отправляет картинку + подпись (caption)
     - Выводит две inline-кнопки: «Поделиться» и «Сначала»
    """
    scores = context.user_data.get('scores', {})
    if not scores:
        return

    winner = max(scores, key=scores.get)
    info = ANIMALS.get(winner, {})

    # Собираем путь до картинки животного
    img_rel = info.get('image', '')
    img_path = os.path.join(MEDIA_DIR, os.path.basename(img_rel))

    caption = (
        f"🎉 Ваше животное — {info.get('name', '')}\n\n"
        f"{info.get('description', '')}\n\n"
        f"Узнать о программе опеки: {info.get('guardian_link', '')}"
    )

    # Отправляем фото, если есть, иначе простой текст
    if os.path.exists(img_path):
        with open(img_path, 'rb') as img:
            await update_or_query.message.reply_photo(photo=img, caption=caption)
    else:
        await update_or_query.message.reply_text(caption)

    # Inline-кнопки после результата
    actions = [
        [InlineKeyboardButton("🔗 Поделиться", switch_inline_query="")],
        [InlineKeyboardButton("🔄 Сначала", callback_data="restart")],
    ]
    await update_or_query.message.reply_text("Что дальше?",
                                            reply_markup=InlineKeyboardMarkup(actions))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает inline-кнопки после результата:
     - contact: сообщает контакты для связи
     - restart: запускает викторину заново
     - feedback: переводит в режим сбора отзыва
    """
    cq = update.callback_query
    await cq.answer()
    data = cq.data

    if data == 'contact':
        # Отправляем контактную информацию напрямую
        contact_text = (
            "По вопросам опекунства звоните по телефону +7 (962) 971-38-75 "
            "или пишите на почту zoofriends@moscowzoo.ru"
        )
        await cq.message.reply_text(contact_text, reply_markup=get_main_kb())

    elif data == 'restart':
        await start_quiz(update, context)

    elif data == 'feedback':
        context.user_data['awaiting_feedback'] = True
        await cq.message.reply_text("Пожалуйста, напишите свой отзыв:")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатия кнопок из MAIN_KEYBOARD и сбор отзывов:
     - «Викторина»: запускает викторину
     - «Отзыв»: включает режим feedback
     - «Связь»: пересылает в поддержку
     - «Помощь»: выводит справку
     - Если в режиме feedback — принимает текст как отзыв
     - Иначе предлагает нажать кнопку или /start
    """
    txt = update.message.text or ''

    if txt == '🧩 Викторина':
        return await start_quiz(update, context)

    if txt == '📝 Отзыв':
        context.user_data['awaiting_feedback'] = True
        return await update.message.reply_text(
            'Напишите, пожалуйста, отзыв:'
        )
    
    if txt == '✉️ Связь':
        # При нажатии на «Связь» выводим контактную информацию
        contact_text = (
            "По вопросам опекунства звоните по телефону +7 (962) 971-38-75 "
            "или пишите на почту zoofriends@moscowzoo.ru"
        )
        return await update.message.reply_text(contact_text, reply_markup=get_main_kb())

    if txt == 'ℹ️ Помощь':
        help_text = (
            '/start — меню\n'
            '🧩 Викторина — начать викторину\n'
            '📝 Отзыв — оставить отзыв\n'
            '✉️ Связь — связаться с поддержкой'
        )
        return await update.message.reply_text(help_text, reply_markup=get_main_kb())

    # Если ждём отзыв, принимаем любой текст как обратную связь
    if context.user_data.get('awaiting_feedback'):
        fb = update.message.text
        # Можно сохранить в файл или БД (но не добавлено)
        context.user_data['awaiting_feedback'] = False
        return await update.message.reply_text('Спасибо за ваш отзыв! 😊',
                                               reply_markup=get_main_kb())

    # Во всех остальных случаях
    await update.message.reply_text('Нажмите кнопку меню или /start',
                                    reply_markup=get_main_kb())

