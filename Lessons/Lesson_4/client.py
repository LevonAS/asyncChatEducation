import os, sys, json
from socket import socket, AF_INET, SOCK_STREAM
from utils import create_presence_message, send_message, get_message, parse_response
from dotenv import load_dotenv


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
        print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((serv_addr, int(listen_port)))
    message_to_server = create_presence_message('Guest')
    send_message(transport, message_to_server)
    try:
        response = get_message(transport)
        print('Ответ сервера: ', response)
        print(parse_response(response))
    except (ValueError, json.JSONDecodeError):
        print('Не удалось декодировать сообщение сервера.')


if __name__ == '__main__':
    client()