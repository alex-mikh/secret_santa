import logging
import random
import asyncio
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

# Команда для начала взаимодействия с ботом и отображения кнопок
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Стартовое меню с кнопкой "Начать"
    keyboard = [
        [InlineKeyboardButton("Начать", callback_data='begin')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Чтобы начать, нажмите кнопку:", reply_markup=reply_markup)

# Обработчик для нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    username = f"@{query.from_user.username}" if query.from_user.username else None

    # Обработка кнопки "Начать"
    if query.data == 'begin':
        if username not in users_started:
            users_started.add(username)  # Помечаем пользователя, что он начал

            # Определение сообщения в зависимости от пола пользователя
            if username in female_users:
                await context.bot.send_message(chat_id=query.from_user.id, text="Сосала?")
            elif username in male_users:
                await context.bot.send_message(chat_id=query.from_user.id, text="Сосал?")
            else:
                await context.bot.send_message(chat_id=query.from_user.id, text="Ты сосал?")

            # Отображение кнопок "Да"
            keyboard = [
                [InlineKeyboardButton("Да", callback_data='yes')],
                [InlineKeyboardButton("Да", callback_data='yes')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("Выберите:", reply_markup=reply_markup)

            await asyncio.sleep(1)

    elif query.data == 'yes':
        # Отправляем сообщение "Харош" и стикер
        await context.bot.send_message(chat_id=query.from_user.id, text="Харош")
        await context.bot.send_sticker(chat_id=query.from_user.id, sticker='CAACAgIAAxkBAAEJ8FxnMefnpbE3LWxYd1v4j7xZmNFuBgACAQADnJy5FPJmUOyrH4j9NgQ')

        # Кнопка для регистрации
        keyboard = [
            [InlineKeyboardButton("Зарегистрироваться", callback_data='register')]
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

        # Регистрация участника
        exclusion = exclusions_dict.get(username, None)
        participants[username] = {
            'to_give': [],
            'to_receive': 0,
            'exclusion': exclusion
        }

        # Сообщение о регистрации
        await query.edit_message_text("Вы зарегистрированы! Ждите, пока все пройдут жеребьевку.")
        await context.bot.send_message(chat_id=561541752, text=f"Пользователь {username} успешно зарегистрировался.")

        # Кнопка для просмотра участников, доступная после регистрации
        keyboard = [
            [InlineKeyboardButton("Посмотреть участников", callback_data='view_participants')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=query.from_user.id, text="Теперь вы можете просмотреть зарегистрированных участников:", reply_markup=reply_markup)

        # Проверка на количество участников для старта жеребьевки
        if len(participants) == 8:
            await start_secret_santa(context)

    # Просмотр зарегистрированных участников
    elif query.data == 'view_participants':
        if participants:
            participant_list = "\n".join(participants.keys())
            await query.message.reply_text(f"Список зарегистрированных участников:\n{participant_list}")
        else:
            await query.message.reply_text("Список участников пока пуст.")

        # Постоянная кнопка для повторного просмотра участников
        keyboard = [
            [InlineKeyboardButton("Посмотреть участников", callback_data='view_participants')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Вы можете снова просмотреть список участников, нажав на кнопку:", reply_markup=reply_markup)

# Функция для жеребьевки
async def start_secret_santa(context):
    # Проверяем, что участников 8
    if len(participants) != 8:
        return

    # Список участников
    usernames = list(participants.keys())
    random.shuffle(usernames)

    # Создаем пары
    for i in range(len(usernames)):
        giver = usernames[i]
        receiver = usernames[(i + 1) % len(usernames)]
        exclusion = participants[giver]['exclusion']

        # Если исключение, меняем пары
        if receiver == exclusion:
            receiver = usernames[(i + 2) % len(usernames)]

        participants[giver]['to_give'].append(receiver)

        # Отправляем каждому пользователю его пару
        user = await participants[giver]
        await user.send_message(f"Вы должны подарить подарок: {receiver}")

    # Уведомляем всех, что жеребьевка завершена
    pair_message = "Пары для проверки:\n"
    for giver, details in participants.items():
        for receiver in details['to_give']:
            pair_message += f"{giver} -> {receiver}\n"

    # Отправляем результат администратору
    await context.bot.send_message(chat_id=561541752, text=pair_message)

# Основная функция для запуска бота
def main():
    API_TOKEN = "7942493404:AAH3lOMj9JqrLVaBULyzuuJAV2Ok4jerA2I"
    application = Application.builder().token(API_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
