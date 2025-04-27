# 🐾 Zoo Totem Bot

**Телеграм-бот-викторина «Тотемное животное»**  
Определяйте своё «тотемное животное» из обитателей Московского зоопарка с помощью короткой викторины, а в конце получите именную картинку, информацию об опеке, возможность поделиться результатом, оставить отзыв или связаться с сотрудниками зоопарка.

---

## 📋 Функции

- **Приветствие и запуск викторины** по команде `/start`  
- **Викторина**: 10 вопросов с вариантами ответа (загружаются из `data/quiz.json`)  
- **Подсчёт баллов** по весам ответов, выбор животного с максимальным количеством баллов  
- **Генерация итоговой картинки** через Pillow: фото животного + имя пользователя + логотип зоопарка  
- **Кнопки действий**:
  - 🔁 «Попробовать ещё раз»  
  - 📢 «Поделиться» в соцсетях  
  - 💬 «Оставить отзыв» (сохранение в `data/feedback.txt`)  
  - 📞 «Связаться» с сотрудниками зоопарка  
- **Логирование** всех ключевых событий в `bot.log`  
- **Автоматические тесты** для главных хендлеров  

---

## 🚀 Установка и запуск

1. **Подготовьте сервер** (Ubuntu/Debian/CentOS и др.):  

    Убедитесь, что установлены Python 3.10+, git и virtualenv:

    ```bash
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip git
    ```

2. **Клонируйте репозиторий и перейдите в папку проекта:**

    ```bash
    cd /opt
    sudo git clone https://github.com/<ваш-username>/zoo_totem_bot.git
    sudo chown -R $USER:$USER zoo_totem_bot
    cd zoo_totem_bot
    ```

3. **Создайте и активируйте виртуальное окружение, установите зависимости:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install --no-cache-dir -r requirements.txt
    ```

4. **Настройте переменные окружения:**

    ```bash
    cp .env.example .env
    # Откройте .env и вставьте ваш BOT_TOKEN:
    # BOT_TOKEN=123456789:ABCDefGhIJKLMnoPQRsT
    ```

5. **Запустите бота как systemd-службу:**

    Создайте файл /etc/systemd/system/zoo_totem_bot.service:

    ```bash
    [Unit]
    Description=ZooTotemBot — Telegram quiz bot
    After=network.target

    [Service]
    Type=simple
    User=<ваш-пользователь>
    WorkingDirectory=/opt/zoo_totem_bot
    ExecStart=/opt/zoo_totem_bot/venv/bin/python -m bot.main
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target
    ```

    Активируйте и запустите службу:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable zoo_totem_bot
    sudo systemctl start zoo_totem_bot
    sudo journalctl -u zoo_totem_bot -f
    ```

После этого бот будет автоматически стартовать на сервере и перезапускаться при сбоях. 
Для проверки отправьте ему /start в Telegram

## 📂 Структура проекта

    zoo_totem_bot/
    ├── bot/
    │   ├── handlers/          # Логика команд и callback-хендлеры
    │   ├── bot.py             # Точка входа
    ├── data/
    │   ├── quiz.json          # Вопросы викторины
    │   ├── animals.json       # Данные о животных
    ├── media/
    │   ├── images/            # Исходные фото животных
    ├── README.md              # Этот файл
    └── bot.log                # Логи бота (в .gitignore)

## 🎮 Использование бота

- **/start — начинает викторину**
- **Отвечайте на вопросы, нажимая inline-кнопки**
- **После последнего вопроса получите:**
    - Текстовый результат с описанием
    - Картинку с вашим тотемом и логотипом
    - Кнопки: «Попробовать ещё раз», «Поделиться», «Оставить отзыв», «Связаться»
