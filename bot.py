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
    '@fedorchenko_alla_a': '@Xitrets_23',
    '@dreadsbliss': '@zeludevdenis',
    '@zeludevdenis': '@dreadsbliss'
}

# Списки девушек и парней
female_users = {'@daryakostritsa', '@kireevapechet', '@acidcoma', '@fedorchenko_alla_a', '@dreadsbliss'}
male_users = {'@alexander_mikh', '@Ivankotans', '@adamovichaa', '@Xitrets_23', '@zeludevdenis'}

# Словарь для хранения данных участников
participants = {}
users_started = set()  # Хранит пользователей, которые нажали "Начать" первый раз
registered_users = {}  # Хранит зарегистрированных пользователей и их ID для отправки сообщений
first_message_id = None  # ID первого сообщения со списком участников

# Команда для начала взаимодействия с ботом и отображения кнопок
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Стартовое меню с кнопкой "Начать"
    keyboard = [
        [InlineKeyboardButton("Начать", callback_data='begin')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Нажми, чтобы начать:", reply_markup=reply_markup)

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
            await asyncio.sleep(0.5)

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
        await asyncio.sleep(0.5)
        await context.bot.send_sticker(chat_id=user_id, sticker='CAACAgIAAxkBAAEJ8FxnMefnpbE3LWxYd1v4j7xZmNFuBgACAQADnJy5FPJmUOyrH4j9NgQ')
        await asyncio.sleep(1.5)

        # Кнопка для регистрации
        keyboard = [
            [InlineKeyboardButton("Нажмите для регистрации", callback_data='register')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Зарегистрироваться:", reply_markup=reply_markup)

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
        await query.edit_message_text("Вы зарегистрировались!")

        # Проверка на количество участников для старта жеребьевки
        if len(participants) == 10:
            await start_secret_santa(context)

        # Отправляем или обновляем сообщение со списком участников для всех зарегистрированных
        await update_participant_list(context)

async def update_participant_list(context):
    # Обновленный список участников
    participant_list = "\n".join(participants.keys())
    text = f"Список участников:\n{participant_list}"

    # Если это первое сообщение, отправляем его и сохраняем ID
    global first_message_id
    if first_message_id is None:
        message = await context.bot.send_message(
            chat_id=list(registered_users.values())[0],  # Отправляем сообщение первому зарегистрированному пользователю
            text=text
        )
        first_message_id = message.message_id  # Сохраняем ID первого сообщения
    else:
        # Редактируем первое сообщение
        await context.bot.edit_message_text(
            chat_id=list(registered_users.values())[0],  # Отправляем сообщение первому зарегистрированному пользователю
            message_id=first_message_id,
            text=text
        )

    # Отправляем или обновляем сообщение со списком для всех зарегистрированных пользователей
    for username, user_id in registered_users.items():
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {username} ({user_id}): {e}")

# async def send_message_to_all_users(context: ContextTypes.DEFAULT_TYPE):
#     # Сообщение для всех пользователей
#     message = "ВРОДЕ ПОПРАВИЛ ХЗ, НАЖМИТЕ ЕЩЕ РАЗ /start ПЛЗ"

#     # Отправка сообщения всем пользователям из списка
#     all_users = female_users.union(male_users)
#     for username in all_users:
#         try:
#             if username in registered_users:
#                 user_id = registered_users[username]
#                 await context.bot.send_message(chat_id=user_id, text=message)
#         except Exception as e:
#             logger.error(f"Ошибка при отправке сообщения пользователю {username}: {e}")

# Обновленный алгоритм жеребьевки
async def start_secret_santa(context):
    # Проверяем, что участников 8
    if len(participants) != 10:
        return

    # Список участников
    usernames = list(participants.keys())
    random.shuffle(usernames)

    # Пытаемся назначить подарки, пока не удастся корректно распределить всех
    while True:
        # Сбрасываем данные для каждого участника перед новой попыткой
        for giver in usernames:
            participants[giver]['to_give'] = []
            participants[giver]['to_receive'] = 0

        success = True

        # Для каждого участника выбираем два уникальных получателя
        for giver in usernames:
            exclusion = participants[giver]['exclusion']

            # Получаем список возможных получателей для текущего участника
            potential_recipients = [u for u in usernames if u != giver and u != exclusion and participants[u]['to_receive'] < 2]

            # Проверяем, чтобы у участника было хотя бы два возможных получателя
            if len(potential_recipients) < 2:
                print(f"Невозможно назначить два подарка для {giver}")
                success = False
                break

            # Назначаем двух уникальных получателей
            recipients = random.sample(potential_recipients, 2)  # Выбираем случайных двух уникальных получателей

            # Назначаем подарки
            participants[giver]['to_give'] = recipients
            for receiver in recipients:
                participants[receiver]['to_receive'] += 1  # Увеличиваем счетчик полученных подарков

        # Если все прошло успешно, выходим из цикла
        if success:
            break
        else:
            print("Повторная попытка жеребьевки...")

    # Отправляем результаты жеребьевки каждому участнику
    for giver, details in participants.items():
        receivers_text = ", ".join(details['to_give'])
        await context.bot.send_message(chat_id=registered_users[giver], text=f"Вы должны подарить подарок этим людям: {receivers_text}")

    # Отправляем результат администратору
    pair_message = "Пары для проверки:\n"
    for giver, details in participants.items():
        for receiver in details['to_give']:
            pair_message += f"{giver} -> {receiver}\n"

    await context.bot.send_message(chat_id=561541752, text=pair_message)

# Ответ на сообщения после регистрации
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = f"@{update.message.from_user.username}" if update.message.from_user.username else None

    # Проверка, что пользователь зарегистрирован
    if username in registered_users:
        await update.message.reply_text("Не пиши сюда")

# Основная функция для запуска бота
def main():
    API_TOKEN = "7942493404:AAH3lOMj9JqrLVaBULyzuuJAV2Ok4jerA2I"
    application = Application.builder().token(API_TOKEN).build()

    # Отправить сообщение всем зарегистрированным пользователям до старта
    # application.add_job(send_message_to_all_users, "interval", minutes=10, context=application)

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
