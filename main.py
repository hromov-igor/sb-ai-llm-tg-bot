#!/usr/bin/env python

import os
import logging
from dotenv import load_dotenv

from langchain_community.chat_models import GigaChat
from langchain.schema import AIMessage, HumanMessage, SystemMessage

import telegram
from telegram.helpers import escape_markdown
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, BotCommand, ReplyKeyboardMarkup

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

#Get tokens from enviroment
load_dotenv()
GIGACHAT_TOKEN = os.environ.get("GIGACHAT_DEFAULT_TOKEN")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")

#List of all models
models = {
    "GigaChat": {
            "model_name": "GigaChat Lite"
    },
    "GigaChat-Plus": {
        "model_name": "GigaChat Lite+"
    },
    "GigaChat-Pro": {
        "model_name": "GigaChat Pro"
    }
}

user_commands = [
    BotCommand("start", "Старт"),
    BotCommand("presets", "Выбрать модель для взаимодействия"),
    BotCommand("clear_context", "Очистить контекст"),
    BotCommand("set_context", "Установить контекст"),
    BotCommand("enable_context", "Включить сохранение контекста"),
    BotCommand("disable_context", "Выключить сохранение контекста"),
    BotCommand("help", "Помощь"),
    BotCommand("info", "Информация о моделях"),
]

async def post_init(application: Application) -> None:
    """Generates menu button with necessary commands"""
    await application.bot.set_my_commands(user_commands)
    await application.bot.set_chat_menu_button()

def check_bot_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if the bot has been restarted"""
    if len(context.user_data) == 0:
        user = context.user_data
        user['model'] = GigaChat(model="GigaChat", credentials=GIGACHAT_TOKEN, verify_ssl_certs=False, scope="GIGACHAT_API_CORP")
        user['model_name'] = "GigaChat Lite"
        user['context'] = []
        user['context_status'] = True
        user['model_info'] = models["GigaChat"]
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the conversation and ask user for input."""
    await update.message.reply_text(
        """Привет\! Это бот для удобной работы с большими языковыми моделями для сотрудников SberAI Lab \nИспользуй команду /help чтобы узнать больше о возможностях бота \nДефолтная модель для запросов: *GigaChat Lite*""",
        parse_mode='MarkdownV2'
    )
    user = context.user_data
    user['model'] = GigaChat(model="GigaChat", credentials=GIGACHAT_TOKEN, verify_ssl_certs=False, scope="GIGACHAT_API_CORP")
    user['model_name'] = "GigaChat Lite"
    user['context'] = []
    user['context_status'] = True
    user['model_info'] = models["GigaChat"]

async def generate_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return generated answer to users post according to a context"""

    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    await update.message.reply_text("Отправляю запрос в "+context.user_data["model_name"])

    messages = []
    if context.user_data['context_status']:
        messages = context.user_data['context']
    messages.append(HumanMessage(content=update.message.text))

    response = context.user_data['model'](messages)

    await update.message.reply_text(escape_markdown(response.content, version=2), parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

    if context.user_data['context_status']:
        context.user_data['context'].append(AIMessage(content=response.content))


async def model_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    msg = "Параметры текущей модели:\n"
    for key, value in context.user_data["model_info"]:
        msg += (str(key) + ": " + str(value))
    await update.message.reply_text(msg)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    await update.message.reply_text("""
Для того, чтобы сделать запрос к выбранной модели просто наберите сообщение в чат

Список доступных команд для использования
/start - запуск бота и приветственное сообщение
/presets - выбор модели для инференса
/help - помощь по боту (эта команда)
/enable_chat_context - включить сохранение контекста для модели
/disable_chat_context - выключить сохранение контекста для модели
/set_chat_context - установить изначальный промпт для модели
/clear_user_context - очистить текущий контекст
/info - описание всех доступный на данный момент моделей
/model_info - подробное описание выбранной в данный момент модели""")


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")

    await update.message.reply_text("""
В данный момент доступны следующие модели для использования:
GigaChat Lite - размер контекста 8192
GigaChat Lite+ - размер контекста 32768
GigaChat Pro - размер контекста 8192""")

async def clear_user_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears current context"""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")

    if not context.user_data["context_status"]:
        await update.message.reply_text("В данный момент сохранение контекста отключено")

    context.user_data["context"] = []
    await update.message.reply_text("Контекст очищен")

async def disable_chat_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disable models context"""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    if not context.user_data["context_status"]:
        await update.message.reply_text("Сохранение контекста уже отключено")
    context.user_data["context_status"] = False
    context.user_data["context"] = []
    await update.message.reply_text("Сохранение контекста отключено")

async def enable_chat_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enables models context"""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    if context.user_data["context_status"]:
        await update.message.reply_text("Сохранение контекста уже включено")
    else:
        context.user_data["context_status"] = True
        context.user_data["context"] = []
        await update.message.reply_text("Сохранение контекста включено")

async def change_model_preset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with list of models to choose from."""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    keyboard = []
    for key, value in models.items():
        keyboard.append([InlineKeyboardButton(value["model_name"], callback_data=key)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите модель:", reply_markup=reply_markup)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

async def model_choice_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    if "GigaChat" in query.data:
        context.user_data["model"] = GigaChat(model=query.data, credentials=GIGACHAT_TOKEN, verify_ssl_certs=False, scope="GIGACHAT_API_CORP")
        model_name = ""
        model = ""
        for key, value in models.items():
            if key == query.data:
                model_name = value["model_name"]
                model = key
        context.user_data["model_name"] = model_name
        context.user_data["model_info"] = models[model]
    await query.edit_message_text(text=f"Выбрана модель: {model_name}")


async def set_chat_context_final(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["context"] = [SystemMessage(content=update.message.text)]
    if context.user_data["context_status"]:
        await update.message.reply_text("Контекст очищен. Установлено сообщение: "+update.message.text)
    if not context.user_data["context_status"]:
        await update.message.reply_text("Сохранение контекста включено. Установлено сообщение: "+update.message.text)

    return ConversationHandler.END

async def set_chat_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    await update.message.reply_text("Введите сообщение, которое хотите использовать как системный контекст. Используйте /cancel для отмены действия")
    return 0

async def cancel_set_chat_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    await update.message.reply_text("Действие отменено")
    return ConversationHandler.END

async def show_current_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    if context.user_data["context_status"]:
        messages = []
        for item in context.user_data["context"]:
            messages.append("**"+str(type(item)).split(".")[-1][:-2]+":** "+item.content)
        if len(messages) == 0:
            await update.message.reply_text("Текущий контекст пуст")
        else:
            await update.message.reply_text("\n".join(messages))
    else:
        await update.message.reply_text("В данный момент сохранение контекста отключено")

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    system_context_handler = ConversationHandler(
        entry_points=[CommandHandler("set_context", set_chat_context)],
        states = {
            0: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_chat_context_final),
                CommandHandler("cancel", cancel_set_chat_context)
            ]
        },
        fallbacks=[]
    )
    application.add_handler(system_context_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("presets", change_model_preset))
    application.add_handler(CallbackQueryHandler(model_choice_button))
    application.add_handler(CommandHandler("clear_context", clear_user_context))
    application.add_handler(CommandHandler("show_current_context", show_current_context))
    application.add_handler(CommandHandler("enable_context", enable_chat_context))
    application.add_handler(CommandHandler("disable_context", disable_chat_context))
    application.add_handler(CommandHandler("model_info", model_info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_answer))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
