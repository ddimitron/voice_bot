ADMIN = ""

HOME_DIR = '/home/student/voice_bot'
LOGS = f'{HOME_DIR}/logs.txt'
DB_FILE = f'{HOME_DIR}/users.db'

IAM_TOKEN_PATH = f'{HOME_DIR}/creds/iam_token.txt'
FOLDER_ID_PATH = f'{HOME_DIR}/creds/folder_id.txt'
BOT_TOKEN_PATH = f'{HOME_DIR}/creds/bot_token.txt'

MAX_USERS = 8
MAX_GPT_TOKENS = 50
COUNT_LAST_MSG = 4

MAX_USER_STT_BLOCKS = 10
MAX_USER_TTS_SYMBOLS = 5000
MAX_USER_GPT_TOKENS = 4000
MAX_TTS_SYMBOLS = 250
AUDIO_BLOCK = 15
MAX_TIME_VOICE = 30

DB_FILE = 'users.db'

SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты учёный по всем предметам мира. Общайся с пользователем на "ты" и используй юмор. '
                                            'Поддерживай диалог. Не объясняй пользователю, что ты умеешь и можешь. '
                                            'Изображай человека'}]