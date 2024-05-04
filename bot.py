import telebot
import logging

from config import ADMIN, COUNT_LAST_MSG, LOGS
from db import prepare_db, add_message, select_n_last_messages
from ya_gpt import ask_gpt
from speechkit import speech_to_text, text_to_speech
from validators import (check_number_of_users,
                        is_stt_block_limit,
                        is_gpt_token_limit,
                        is_tts_symbol_limit
                        )
from untils import get_bot_token
bot = telebot.TeleBot(get_bot_token())

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOGS,
    filemode="w",
)


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id,
                     "Привет! Я бот голосовой помощник напиши /help ")


@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.from_user.id,
                     "Чтобы приступить к общению, "
                     "отправь мне голосовое сообщение или "
                     "текст или напиши команды:\n"
                     "/tts - для проверки проверки озвучивания текста\n"
                     "/stt - для проверки проверки перевода "
                     "голосового сообщения в текст\n"
                     "/reverse_info - для написания обратной связи")


@bot.message_handler(commands=["debug"])
def send_logs(message):
    user_id = message.chat.id
    if user_id == ADMIN:
        with open("log_file.txt", "rb") as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.send_message(user_id, "У вас недостаточно прав")


@bot.message_handler(commands=["reverse_info"])
def reception_back_info(message):
    bot.send_message(message.chat.id, "Напиши обратную связь:")
    bot.register_next_step_handler(message, send_back_info)


def send_back_info(message):
    bot.send_message(ADMIN, f"От юзера {message.chat.id} "
                            f"отправлена обратная информация:\n {message.text}")


@bot.message_handler(commands=['tts'])
def tts_handler(message):
    user_id = message.chat.id
    bot.send_message(user_id,
                     'Отправь следующим сообщением текст, чтобы я его озвучил!')

    bot.register_next_step_handler(message, tts)


def tts(message):

    user_id = message.chat.id
    text = message.text
    try:
        if message.content_type != 'text':
            bot.send_message(user_id, 'Отправь текстовое сообщение')
            return

        text_symbol = is_tts_symbol_limit(message, text)
        if text_symbol is None:
            return

        add_message(user_id, full_message=[text, 'user_tts', 0, text_symbol, 0])
        status, content = text_to_speech(text)

        if status:
            bot.send_voice(user_id, content)
        else:
            bot.send_message(user_id, content)

    except:
        logging.debug('Error in telebot')


@bot.message_handler(commands=['stt'])
def stt_handler(message):
    user_id = message.chat.id

    bot.send_message(user_id,
                     'Отправь голосовое сообщение, '
                     'чтобы я его преобразил в текст!')

    bot.register_next_step_handler(message, stt)


def stt(message):
    user_id = message.chat.id
    if message.content_type != 'voice':
        bot.send_message(user_id, 'Отправь голосовое сообщение')
        bot.register_next_step_handler(message, stt_handler)

    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    duration = message.voice.duration
    audio_blocks = is_stt_block_limit(user_id, duration)

    if audio_blocks is None:
        return

    status, text = speech_to_text(file)

    if status:
        add_message(user_id,
                    full_message=[text, 'user_stt', 0, 0, audio_blocks])
        bot.send_message(user_id, text, reply_to_message_id=message.id)
    else:
        bot.send_message(user_id, text)


# обрабатываем голосовые сообщения
@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.chat.id
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return

        audio_blocks, error_message = is_stt_block_limit(user_id,
                                                       message.voice.duration)

        if error_message:
            bot.send_message(user_id, error_message)
            return

        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)

        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return

        add_message(user_id=user_id,
                    full_message=[stt_text, 'user', 0, 0, audio_blocks])

        last_messages, total_spent_tokens = select_n_last_messages(user_id,
                                                                COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages,
                                                             total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)

        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer

        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)

        add_message(user_id=user_id,
                    full_message=[answer_gpt, 'assistant', total_gpt_tokens,
                                  tts_symbols, 0])

        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_tts, voice_response = text_to_speech(answer_gpt)
        if status_tts:
            bot.send_voice(user_id, voice_response,
                           reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, answer_gpt,
                             reply_to_message_id=message.id)

        status_tts, voice_response = text_to_speech(answer_gpt)
        if not status_tts:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
        else:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)

    except Exception as e:
        logging.error(e)
        bot.send_message(message.chat.id,
                    "Не получилось ответить. Попробуй записать другое сообщение")


# обрабатываем текстовые сообщения
@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        user_id = message.from_user.id

        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return

        add_message(user_id=user_id,
                    full_message=[message.text, 'user', 0, 0, 0])

        last_messages, total_spent_tokens = select_n_last_messages(user_id,
                                                                   COUNT_LAST_MSG)

        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages,
                                                             total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer

        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)

        bot.send_message(user_id, answer_gpt,
                         reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)  # если ошибка — записываем её в логи
        bot.send_message(message.chat.id,
                         "Не получилось ответить. Попробуй написать другое сообщение")


@bot.message_handler(func=lambda: True)
def handler(message):
    bot.send_message(message.chat.id,
                     "Отправь мне голосовое или текстовое сообщение, и я тебе отвечу")


if __name__ == "__main__":
    bot.infinity_polling()
    logging.info("The bot is running")
    prepare_db()