import logging
import requests

from untils import get_creds
from config import LOGS

iam_token, folder_id = get_creds()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOGS,
    filemode="w",
)


def text_to_speech(text):

    headers = {
        'Authorization': f'Bearer {iam_token}',
    }
    data = {
        'text': text,
        'lang': 'ru-RU',
        'voice': 'zahar',
        'folderId': folder_id,
    }
    # Выполняем запрос
    response = requests.post(
        'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize',
        headers=headers,
        data=data
    )
    if response.status_code == 200:
        return True, response.content
    else:
        return False, logging.debug("При запросе в SpeechKit возникла ошибка")


def speech_to_text(data):

    params = "&".join([
        "topic=general",
        f"folderId={folder_id}",
        "lang=ru-RU"
    ])

    headers = {
        'Authorization': f'Bearer {iam_token}',
    }
    url = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}"

    response = requests.post(url=url, headers=headers, data=data)

    decoded_data = response.json()
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")

    else:
        return False, "ОШИБКА"