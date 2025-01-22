import os
from dotenv import load_dotenv

load_dotenv()
GIGACHAT_TOKEN = os.environ.get("GIGACHAT_DEFAULT_TOKEN")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPEN_AI_TOKEN = os.environ.get("OPEN_AI_TOKEN")
MAX_MSG_LEN = 4096

models = {
    "GigaChat": {
        "display_model_name": "GigaChat",
        "model_context_max_len": 32768,
    },
    "GigaChat-Pro": {
        "display_model_name": "GigaChat Pro",
        "model_context_max_len": 32768,
    },
    "gpt-4o": {
        "display_model_name": "ChatGPT 4o",
        "model_context_max_len": 128000,
    },
    "gpt-4o-mini": {
        "display_model_name": "ChatGPT 4o-mini",
        "model_context_max_len": 128000,
    }
}
