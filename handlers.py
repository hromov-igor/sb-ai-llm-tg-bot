import telegram
from telegram.helpers import escape_markdown
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    BotCommand,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from langchain_community.chat_models import GigaChat
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from config import (
    GIGACHAT_TOKEN,
    OPEN_AI_TOKEN,
    MAX_CONTEXT_LEN,
    MAX_MSG_LEN,
    models
)

async def post_init(bot: telegram.Bot) -> None:
    """Generates menu button with necessary commands"""
    
    user_commands = [
        BotCommand("start", "Старт"),
        BotCommand("presets", "Выбрать модель для взаимодействия"),
        BotCommand("help", "Помощь"),
        BotCommand("clear_context", "Очистить контекст"),
        BotCommand("set_context", "Установить контекст"),
        BotCommand("enable_context", "Включить сохранение контекста"),
        BotCommand("disable_context", "Выключить сохранение контекста"),
        BotCommand("show_current_context", "Показать текущий контекст")
    ]
    
    await bot.set_my_commands(user_commands)
    await bot.set_chat_menu_button()
    
async def check_bot_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the bot has been restarted"""
    
    await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
    await post_init(context.bot)
    
    if len(context.user_data) == 0:
        user = context.user_data
        user['model'] = GigaChat(model="GigaChat", credentials=GIGACHAT_TOKEN, verify_ssl_certs=False, scope="GIGACHAT_API_CORP")
        user['display_model_name'] = "GigaChat Lite"
        user['context'] = []
        user['context_status'] = True
        user['model_info'] = models["GigaChat"]
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the conversation, init default parameters, run post_init characters"""
    await update.message.reply_text(
        """Привет\! Это бот для удобной работы с большими языковыми моделями\nИспользуй команду /help чтобы узнать больше о возможностях бота \nДефолтная модель для запросов: *GigaChat*""",
        parse_mode='MarkdownV2'
    )
    user = context.user_data
    user['model'] = GigaChat(model="GigaChat", credentials=GIGACHAT_TOKEN, verify_ssl_certs=False, scope="GIGACHAT_API_CORP")
    user['display_model_name'] = "GigaChat"
    user['context'] = []
    user['context_status'] = True
    user['model_info'] = models["GigaChat"]

async def generate_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return generated answer to users post according to a context"""

    await check_bot_restart(update, context)
    
    await update.message.reply_text("Отправляю запрос в "+context.user_data["display_model_name"])
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    messages = []
    if context.user_data['context_status']:
        messages = context.user_data['context']
    messages.append(HumanMessage(content=update.message.text))

    total_len = 0
    tmp_messages = []
    for item in messages[::-1]:
        if total_len + len(item.content) < MAX_CONTEXT_LEN:
            total_len += len(item.content)
            tmp_messages.append(item)
    messages = tmp_messages

    response = context.user_data['model'].invoke(messages)

    for i in range(0, len(response.content), MAX_MSG_LEN):
        text_to_send = response.content[i:i + MAX_MSG_LEN]
        try:
            await update.message.reply_text(text_to_send, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, write_timeout=300)
        except Exception as e:
            await update.message.reply_text(escape_markdown(text_to_send, version=2), parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, write_timeout=300)

    if context.user_data['context_status']:
        context.user_data['context'].append(AIMessage(content=response.content))


async def model_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
        await post_init(context.bot)
    msg = "Параметры текущей модели:\n"
    for key, value in context.user_data["model_info"]:
        msg += (str(key) + ": " + str(value))
    await update.message.reply_text(msg)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
        await post_init(context.bot)
    await update.message.reply_text("""
Для того, чтобы сделать запрос к выбранной модели просто наберите сообщение в чат

Список доступных команд для использования
/start - запуск бота и приветственное сообщение
/presets - выбор модели для инференса
/help - помощь по боту (эта команда)
/enable_context - включить сохранение контекста для модели
/disable_context - выключить сохранение контекста для модели
/set_context - установить изначальный (системный) контекст для модели
/show_current_context - показать текущий контекст
/clear_context - очистить текущий контекст
""")

async def clear_user_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears current context"""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
        await post_init(context.bot)
    if not context.user_data["context_status"]:
        await update.message.reply_text("В данный момент сохранение контекста отключено")

    context.user_data["context"] = []
    await update.message.reply_text("Контекст очищен")

async def disable_chat_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disable models context"""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
        await post_init(context.bot)

    if not context.user_data["context_status"]:
        await update.message.reply_text("Сохранение контекста уже отключено")
    context.user_data["context_status"] = False
    context.user_data["context"] = []
    await update.message.reply_text("Сохранение контекста отключено")

async def enable_chat_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enables models context"""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
        await post_init(context.bot)

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
        await post_init(context.bot)

    keyboard = []
    for key, value in models.items():
        keyboard.append([InlineKeyboardButton(value["display_model_name"], callback_data=key)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите модель:", reply_markup=reply_markup)

async def model_choice_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
        await post_init(context.bot)

    query = update.callback_query

    await query.answer()
    if "gpt" in query.data:
        context.user_data["model"] = ChatOpenAI(model_name=query.data, openai_api_key=OPEN_AI_TOKEN)
        for key, value in models.items():
            if key == query.data:
                model_name = value["display_model_name"]
                model = key
        context.user_data["display_model_name"] = model_name
        context.user_data["model_info"] = models[model]
    if "GigaChat" in query.data:
        context.user_data["model"] = GigaChat(model=query.data, credentials=GIGACHAT_TOKEN, verify_ssl_certs=False, scope="GIGACHAT_API_CORP")
        model_name = ""
        model = ""
        for key, value in models.items():
            if key == query.data:
                model_name = value["display_model_name"]
                model = key
        context.user_data["display_model_name"] = model_name
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
        await post_init(context.bot)

    await update.message.reply_text("Введите сообщение, которое хотите использовать как системный контекст. Используйте /cancel для отмены действия")
    return 0

async def cancel_set_chat_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
        await post_init(context.bot)

    await update.message.reply_text("Действие отменено")
    return ConversationHandler.END

async def show_current_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if check_bot_restart(update, context):
        await update.message.reply_text("Бот был перезапущен. Применены стандартные настройки")
        await post_init(context.bot)

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
