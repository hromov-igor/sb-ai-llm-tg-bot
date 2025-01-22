#!/usr/bin/env python

from config import TELEGRAM_BOT_TOKEN

from telegram import Update

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from telegram.ext import Application
from handlers import start, generate_answer, clear_user_context, help, change_model_preset, set_chat_context, clear_user_context, model_choice_button, show_current_context, enable_chat_context, disable_chat_context, model_info, set_chat_context_final, cancel_set_chat_context

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
