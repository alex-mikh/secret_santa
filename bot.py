import logging
import random
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Словарь исключений для тайного санты
exclusions_dict = {
    '@alexander_mikh': '@daryakostritsa',
    '@daryakostritsa': '@alexander_mikh',
    '@Ivankotans': '@kireevapechet',
    '@kireevapechet': '@Ivankotans',
    '@adamovichaa': '@acidcoma',
    '@acidcoma': '@adamovichaa',
    '@Xitrets_23': '@fedorchenko_alla_a',
    '@fedorchenko_alla_a': '@Xitrets_23'
}

# Списки девушек и парней
female_users = {'@daryakostritsa', '@kireevapechet', '@acidcoma', '@fedorchenko_alla_a'}
male_users = {'@alexander_mikh', '@Ivankotans', '@adamovichaa', '@Xitrets_23'}

# Словарь для хранения данных участников
participants = {}
users_started = set()  # Хранит пользователей, которые нажали "Начать" первый раз
registration_file = "registered_users.txt"  # Имя файла для хранения зарегистрированных участников

# Команда для начала взаимодействия с ботом и отображения кнопок
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = f"@{update.message.from_user.username}" if update.message.from_user.username else None

    # Проверяем, нажимал ли пользователь кнопку ранее
    if username not in users_started:
        # Добавляем пользователя в список тех, кто нажал "Начать"
        users_started.add(username)

        # Создаем меню с кнопкой "Начать"
        keyboard = [
            [InlineKeyboardButton("Начать", callback_data='begin')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Добро пожаловать! Чтобы начать, нажмите кнопку:", reply_markup=reply_markup)
    else:
        # Сообщение, если пользователь уже нажимал "Начать"
        await update.message.reply_text("Вы уже начали! Зарегистрируйтесь, если еще не сделали этого.")

# Обработчик для нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    username = f"@{query.from_user.username}" if query.from_user.username else None

    # Обработка кнопки "Начать"
    if query.data == 'begin':
        if username not in users_started:
            users_started.add(username)  # Помечаем пользователя, что он начал
            
            # Удаляем приветственное сообщение и кнопку
            await query.message.delete()

            # Показ основного меню для регистрации
            keyboard = [
                [InlineKeyboardButton("Зарегистрироваться", callback_data='register')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("Теперь вы можете зарегистрироваться:", reply_markup=reply_markup)

    # Регистрация пользователя
    elif query.data == 'register':
        user = query.from_user
        username = f"@{user.username}" if user.username else None

        if not username:
            await query.edit_message_text("Для участия необходимо иметь имя пользователя в Telegram!")
            return

        exclusion = exclusions_dict.get(username, None)
        participants[username] = {
            'to_give': [],
            'to_receive': 0,
            'exclusion': exclusion
        }

        # Обновляем или создаем .txt файл с зарегистрированными участниками
        await update_registration_file(username)

        # Отправляем сообщение, что пользователь зарегистрирован
        await query.edit_message_text("Вы зарегистрированы! Ждите, пока все пройдут жеребьевку.")

        # Если все 8 участников зарегистрировались, начинаем жеребьевку
        if len(participants) == 8:
            await start_secret_santa(context)

# Функция для обновления файла зарегистрированных участников
async def update_registration_file(username):
    # Проверяем, существует ли файл. Если нет, создаем его
    if not os.path.exists(registration_file):
        with open(registration_file, "w") as file:
            file.write("Список зарегистрированных участников:\n")

    # Добавляем нового участника в файл
    with open(registration_file, "a") as file:
        file.write(f"{username}\n")

# Функция для жеребьевки
async def start_secret_santa(context):
    # Проверяем, что участников 8
    if len(participants) != 8:
        return

    # Список участников
    usernames = list(participants.keys())

    # Перемешиваем список
    random.shuffle(usernames)

    # Создаем пары
    for i in range(len(usernames)):
        giver = usernames[i]
        receiver = usernames[(i + 1) % len(usernames)]  # Следующий элемент в списке, последний дарит первому
        exclusion = participants[giver]['exclusion']

        # Если исключение, меняем пары
        if receiver == exclusion:
            receiver = usernames[(i + 2) % len(usernames)]  # Сдвигаем пару на два

        participants[giver]['to_give'].append(receiver)

        # Отправляем каждому пользователю его пару
        user = await participants[giver]
        await user.send_message(f"Вы должны подарить подарок: {receiver}")

    # Уведомляем всех, что жеребьевка завершена
    for user in participants:
        await user.send_message(f"Жеребьевка завершена! Вам нужно подарить подарки следующим людям: {participants[user]['to_give']}")
    pair_message = "Пары для проверки:\n"
    for giver, details in participants.items():
        for receiver in details['to_give']:
            pair_message += f"{giver} -> {receiver}\n"

    # Отправляем результат администратору
    await context.bot.send_message(chat_id='@alexander_mikh', text=pair_message)

# Основная функция для запуска бота
def main():
    # Ваш API token
    API_TOKEN = "7942493404:AAH3lOMj9JqrLVaBULyzuuJAV2Ok4jerA2I"

    application = Application.builder().token(API_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))  # Обработчик нажатий кнопок
    application.run_polling()

if __name__ == "__main__":
    main()
