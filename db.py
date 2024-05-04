import sqlite3
import logging

from config import DB_FILE, LOGS

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOGS,
    filemode="w",
)


def create_db():
    connection = sqlite3.connect("users.db")
    logging.info("Connecting to the database")
    connection.close()


def execute_query(sql_query, data=None, db_path=DB_FILE):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)

    connection.commit()
    connection.close()


def execute_selection_query(sql_query, data=None, db_path=DB_FILE):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)
    result = cursor.fetchall()
    connection.close()
    return result


def create_table():
    try:
        sql_query = (
            f"CREATE TABLE IF NOT EXISTS users"
            f"(id INTEGER PRIMARY KEY, "
            f"user_id INTEGER, "
            f"message TEXT,"
            f"role TEXT,"
            f"total_gpt_tokens INTEGER,"
            f"audio_blocks INTEGER,"
            f"tts_symbols INTEGER);"
        )

        execute_query(sql_query)
    except:
        logging.debug('An error occurred in creating the table')


def add_message(user_id, full_message):
    try:
        message, role, total_gpt_tokens, tts_symbols, stt_blocks = full_message
        sql_query = ('''
                    INSERT INTO users (user_id, message, role, 
                    total_gpt_tokens, tts_symbols, audio_blocks) 
                    VALUES (?, ?, ?, ?, ?, ?)'''
                     )

        data = (user_id, message, role, total_gpt_tokens, tts_symbols,
                stt_blocks)
        execute_query(sql_query, data=data)

        logging.info(f"DATABASE: INSERT INTO messages "
                     f"VALUES ({user_id}, {message}, {role}, "
                     f"{total_gpt_tokens}, {tts_symbols}, {stt_blocks})")

    except Exception as e:

        logging.error(e)
        return None


# считаем количество уникальных пользователей помимо самого пользователя
def count_users(user_id):
    try:
        sql_query = ('''SELECT COUNT(DISTINCT user_id) FROM users
                    WHERE user_id <> ?''')
        result = execute_selection_query(sql_query, data=(user_id,))
        return result[0][0]

    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return None


def select_n_last_messages(user_id, n_last_messages):
    messages = []
    total_spent_tokens = 0
    try:
        sql_query = ('''
        SELECT message, role, total_gpt_tokens FROM users 
        WHERE user_id=? AND (role="user" OR role="assistant" OR role="system")
        ORDER BY id DESC LIMIT ?''')
        data = (user_id, n_last_messages)
        result = execute_selection_query(sql_query, data)
        if result and result[0][0]:

            for message in reversed(data):
                messages.append({'text': message[0], 'role': message[1]})
                total_spent_tokens = max(total_spent_tokens, message[2])

        return messages, total_spent_tokens

    except Exception as e:
        logging.error(e)
        return messages, total_spent_tokens


def count_all_limits(user_id, limit_type):
    try:
        sql_query = (
            f'''SELECT SUM({limit_type}) FROM users WHERE user_id=?'''
        )
        data = (user_id, )
        result = execute_selection_query(sql_query, data)
        if result and result[0][0]:
            logging.info(f"DATABASE: У user_id={user_id} использовано "
                         f"{data[0]} {limit_type}")
            return result[0][0]
        else:
            return 0  # возвращаем 0
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return 0


def prepare_db():
    create_db()
    create_table()
