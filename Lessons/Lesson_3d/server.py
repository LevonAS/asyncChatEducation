import os
from socket import AF_INET, SOCK_STREAM, socket
import sys
from utils import Utils


def main():
    utils = Utils()

    global server_address, server_port
    try:
        if sys.argv[1] == '-a' and sys.argv[3] == '-p':
            head, a, server_address, p, server_port, *tail = sys.argv
            print(f'Сервер запущен!\nАдрес: {server_address} Порт: {server_port}\n'
                  f'Для выхода нажмите CTRL+C')
        else:
            raise NameError
    except (IndexError, NameError):
        server_address = os.getenv('DEFAULT_IP_ADDRESS')
        server_port = os.getenv('DEFAULT_PORT')
        print('DEFAULT_IP_ADDRESS: ', server_address)
        print('PORT: ', server_port)
        print(f'Сервер запущен с настройками по умолчанию!\n'
              f'Адрес: {server_address} Порт: {server_port}\n'
              f'Для более точной кнфигурации задайте адресс и порт сервера: '
              f'$ python3 server.py -a [ip-адрес] -p [порт сервера]\n\n'
              f'Для выхода нажмите CTRL+C\n')

    transport = socket(AF_INET, SOCK_STREAM)
    transport.bind((server_address, int(server_port)))
    transport.listen(int(os.getenv('MAX_CONNECTIONS')))

    while True:
        client, address = transport.accept()
        message = utils.get_message(client)
        response = utils.parse_message(message)
        utils.send_message(client, response)
        client.close()

        print(f'Запрос от клиента: {message}\n'
              f'Код ответа для клиента: {response}')


if __name__ == '__main__':
    main()
    