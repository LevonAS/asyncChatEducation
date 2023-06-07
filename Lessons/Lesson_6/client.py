import os, sys, json
from socket import socket, AF_INET, SOCK_STREAM
import logging
import log.client_log_config
from utils import create_presence_message, send_message, get_message, parse_response
from dotenv import load_dotenv


# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')

def client():
    load_dotenv()

    global serv_addr, listen_port

    try:
        if sys.argv[1] and sys.argv[2]:
            serv_addr, listen_port = sys.argv[1], sys.argv[2]
            if int(listen_port) < 1024 or int(listen_port) > 65535:
                raise ValueError
    except IndexError:
        serv_addr, listen_port = os.getenv(
            'DEFAULT_IP_ADDRESS'), os.getenv('DEFAULT_PORT')
    except ValueError:
        CLIENT_LOGGER.critical(
            'В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((serv_addr, int(listen_port)))
    message_to_server = create_presence_message('Guest')
    send_message(transport, message_to_server)
    try:
        response = get_message(transport)
        CLIENT_LOGGER.info('Ответ сервера: ', response)
        CLIENT_LOGGER.debug(parse_response(response))
    except (ValueError, json.JSONDecodeError):
        CLIENT_LOGGER.error('Не удалось декодировать сообщение сервера.')


if __name__ == '__main__':
    client()