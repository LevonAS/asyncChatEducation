import os, time, json
from log.decor_log import log


@log
def send_message(open_socket, message):
    json_message = json.dumps(message)
    response = json_message.encode(os.getenv('ENCODING'))
    open_socket.send(response)
    # print("UUU_SM_1", "[message:]", message, "\n[response:]", response, "\n[open_socket:]", open_socket, "\n")

@log
def get_message(client):
    """
    Утилита приёма и декодирования сообщения принимает байты выдаёт словарь,
    если приняточто-то другое отдаёт ошибку значения
    :param client:
    :return:
    """
    response = client.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
    # print("UUU_GM_1", response, "||||")
    if isinstance(response, bytes):
        json_response = response.decode(os.getenv('ENCODING'))
        response_dict = json.loads(json_response)
        if isinstance(response_dict, dict):
            # print("UUU_GM_2", response_dict, "||||")
            return response_dict
        raise ValueError
    raise ValueError


# @log
# def pcm(message, messages_list, client):
#     """
#     Обработчик сообщений от клиентов, принимает словарь - сообщение от клинта,
#     проверяет корректность, отправляет словарь-ответ для клиента с результатом приёма.
#     :param message:
#     :param messages_list:
#     :param client:
#     :return:
#     """
#     # print("UUU_PCM_1", "[message:]", message, "\n[messages_list:]", messages_list, "\n[client:]", client, "\n")
#     # SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
#     # Если это сигнал о присутствии, принимаем и отвечаем
#     if os.getenv('ACTION') in message \
#             and message[os.getenv('ACTION')] == os.getenv('PRESENCE') \
#             and os.getenv('TIME') in message \
#             and os.getenv('USER') in message \
#             and message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')] == 'Guest':
#         send_message(client, {os.getenv('RESPONSE'): 200})
#         # print("UUU_PCM_2","send_message RESPONSE", "||||", client)
#         return
#     # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
#     elif os.getenv('ACTION') in message \
#             and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
#             and os.getenv('TIME') in message \
#             and os.getenv('MESSAGE_TEXT') in message:
#         messages_list.append((
#             message[os.getenv('ACCOUNT_NAME')], 
#             message[os.getenv('MESSAGE_TEXT')]
#         ))
#         # print("UUU_PCM_3", "[message:]", message, "\n[messages_list:]", messages_list, "\n[client:]", client, "\n")
#         return
#     # Иначе отдаём Bad request
#     else:
#         send_message(client, {
#             os.getenv('RESPONSE'): 400,
#             os.getenv('ERROR'): 'Bad Request'
#         })
#         return

@log
def create_presence_message(account_name):
    """Функция генерирует запрос о присутствии клиента"""
    message = {
        os.getenv('ACTION'): os.getenv('PRESENCE'),
        os.getenv('TIME'): time.time(),
        os.getenv('USER'): {
            os.getenv('ACCOUNT_NAME'): account_name
        }
    }
    # CLIENT_LOGGER.debug(f"Сформировано {os.getenv('PRESENCE')} сообщение для пользователя {account_name}")
    return message

@log
def parse_response(message):
    """
    Функция разбирает ответ сервера на сообщение о присутствии,
    возращает 200 если все ОК или генерирует исключение при ошибке
    """
    # CLIENT_LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if os.getenv('RESPONSE') in message:
        if message[os.getenv('RESPONSE')] == 200:
            return 200
        elif message[os.getenv('RESPONSE')] == 409:
            return 409
        return 400
    raise ValueError
        