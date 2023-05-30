import os, sys, json
from socket import socket, AF_INET, SOCK_STREAM
from utils import get_message, parse_message, send_message
from dotenv import load_dotenv


def server():
    load_dotenv()
    global serv_addr, listen_port
    try:
        if sys.argv[1] == '-a' and sys.argv[3] == '-p':
            head, a, serv_addr, p, listen_port, *tail = sys.argv
            if int(listen_port) < 1024 or int(listen_port) > 65535:
                raise ValueError
            print(f'Сервер запущен!\n'
                  f'Адрес: {serv_addr} Порт: {listen_port}\n'
                  f'Для выхода нажмите CTRL+C\n')
        else:
            raise NameError
    except (IndexError, NameError):
        serv_addr = os.getenv('DEFAULT_IP_ADDRESS')
        listen_port = os.getenv('DEFAULT_PORT')
        print(f'Сервер запущен с настройками по умолчанию!\n'
              f'Адрес: {serv_addr} Порт: {listen_port}\n'
              f'Для ручных настроек подключения используйте аргументы командной строки:\n'
              f'$ python server.py -a [ip-адрес] -p [порт сервера]\n\n'
              f'Для выхода нажмите CTRL+C\n')
    except ValueError:
        print(
            'В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)


    transport = socket(AF_INET, SOCK_STREAM)
    transport.bind((serv_addr, int(listen_port)))
    transport.listen(int(os.getenv('MAX_CONNECTIONS')))

    while True:
        try:
            client, client_address = transport.accept()
            message = get_message(client)
            response = parse_message(message)
            send_message(client,  response)
            client.close()

            print(f'Запрос от клиента {client_address}:\n {message}\n'
                  f'Код ответа клиенту: {response}')
        except (ValueError, json.JSONDecodeError):
            print('Принято некорретное сообщение от клиента!')
            client.close()


if __name__ == '__main__':
    server()
    