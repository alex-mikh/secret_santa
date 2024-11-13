import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

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
registered_users = {}  # Хранит зарегистрированных пользователей и их ID для отправки сообщений

# Команда для начала взаимодействия с ботом и отображения кнопок
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Стартовое меню с кнопкой "Начать"
    keyboard = [
        [InlineKeyboardButton("Начать", callback_data='begin')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Жми сюда:", reply_markup=reply_markup)

# Обработчик для нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    username = f"@{query.from_user.username}" if query.from_user.username else None
    user_id = query.from_user.id

    # Обработка кнопки "Начать"
    if query.data == 'begin':
        if username not in users_started:
            users_started.add(username)  # Помечаем пользователя, что он начал

            # Определение сообщения в зависимости от пола пользователя
            if username in female_users:
                text = "Сосала?"
            elif username in male_users:
                text = "Сосал?"
            else:
                text = "Ты сосал?"
            
            # Отправляем сообщение перед кнопками
            await context.bot.send_message(chat_id=user_id, text=text)

            # Пауза перед отправкой кнопок "Да"
            await asyncio.sleep(1)

            # Отправляем кнопки "Да" после сообщения "Сосал?"
            keyboard = [
                [
                    InlineKeyboardButton("Да", callback_data='yes'),
                    InlineKeyboardButton("Да", callback_data='yes')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=user_id, text="Выберите вариант:", reply_markup=reply_markup)

    elif query.data == 'yes':
        # Отправляем сообщение "Харош" и стикер
        await context.bot.send_message(chat_id=user_id, text="Харош")
        await asyncio.sleep(0.3)
        await context.bot.send_sticker(chat_id=user_id, sticker='CAACAgIAAxkBAAEJ8FxnMefnpbE3LWxYd1v4j7xZmNFuBgACAQADnJy5FPJmUOyrH4j9NgQ')
        await asyncio.sleep(2)

        # Кнопка для регистрации
        keyboard = [
            [InlineKeyboardButton("Зарегистрироваться", callback_data='register')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Регайся:", reply_markup=reply_markup)

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
        registered_users[username] = user_id  # Сохраняем ID пользователя

        # Сообщение о регистрации
        await query.edit_message_text("Зарегался, харош!")

        # Проверка на количество участников для старта жеребьевки
        if len(participants) == 8:
            await start_secret_santa(context)

        # Отправляем или обновляем сообщение со списком участников для всех зарегистрированных
        await update_participant_list(context)

async def update_participant_list(context):
    # Обновленный список участников
    participant_list = "\n".join(participants.keys())
    text = f"Кто еще зарегался:\n{participant_list}"

    # Отправляем или обновляем сообщение со списком для каждого зарегистрированного пользователя
    for username, user_id in registered_users.items():
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {username} ({user_id}): {e}")

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
        await context.bot.send_message(chat_id=registered_users[giver], text=f"Вы должны подарок этим людям: {receiver}")

    # Уведомляем всех, что жеребьевка завершена
    pair_message = "Пары для проверки:\n"
    for giver, details in participants.items():
        for receiver in details['to_give']:
            pair_message += f"{giver} -> {receiver}\n"

    # Отправляем результат администратору
    await context.bot.send_message(chat_id=561541752, text=pair_message)

# Ответ на сообщения после регистрации
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = f"@{update.message.from_user.username}" if update.message.from_user.username else None

    # Проверка, что пользователь зарегистрирован
    if username in registered_users:
        await update.message.reply_text("не пиши сюда")

# Основная функция для запуска бота
def main():
    API_TOKEN = "7942493404:AAH3lOMj9JqrLVaBULyzuuJAV2Ok4jerA2I"
    application = Application.builder().token(API_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
