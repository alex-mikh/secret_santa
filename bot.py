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

# Словарь для хранения данных участников
participants = {}
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
        # Пауза перед кнопками "Да"
        await asyncio.sleep(1)

        # Отправляем кнопки "Да"
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='yes')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text="Сосал?", reply_markup=reply_markup)

    elif query.data == 'yes':
        # Отправляем сообщение "Харош" и кнопку для регистрации
        await context.bot.send_message(chat_id=user_id, text="Харош!")
        await asyncio.sleep(2)
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
        participants[username] = {'to_give': [], 'to_receive': 0, 'exclusion': exclusion}
        registered_users[username] = user_id  # Сохраняем ID пользователя

        # Сообщение о регистрации
        await query.edit_message_text("Зарегался, харош!")

        # Проверка на количество участников для старта жеребьевки
        if len(participants) == 8:
            await start_secret_santa(context)

        # Отправляем обновленный список участников для всех
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

    # Создаем пары, чтобы каждый дарил двум уникальным участникам и получал от двух
    for giver in usernames:
        assigned_recipients = 0
        exclusion = participants[giver]['exclusion']

        # Получаем список возможных получателей для текущего участника
        potential_recipients = [u for u in usernames if u != giver and u != exclusion and u not in participants[giver]['to_give']]
        
        # Назначаем двух получателей
        while assigned_recipients < 2 and potential_recipients:
            receiver = potential_recipients.pop(0)

            if participants[receiver]['to_receive'] < 2:  # Проверяем, что получатель не получил 2 подарка
                participants[giver]['to_give'].append(receiver)
                participants[receiver]['to_receive'] += 1
                assigned_recipients += 1

        if assigned_recipients < 2:
            logger.error(f"Ошибка жеребьевки для {giver}: недостаточно уникальных получателей")

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
