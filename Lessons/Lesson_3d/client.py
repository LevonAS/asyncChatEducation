import os
import sys
from socket import AF_INET, SOCK_STREAM, socket
from utils import Utils


def main():
    utils = Utils()

    global server_address, server_port

    try:
        if sys.argv[1] and sys.argv[2]:
            server_address, server_port = sys.argv[1], sys.argv[2]
    except IndexError:
        server_address, server_port = os.getenv(
            'DEFAULT_IP_ADDRESS'), os.getenv('DEFAULT_PORT')

    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((server_address, int(server_port)))
    presence_message = utils.create_presence_message('Guest')
    utils.send_message(transport, presence_message)
    response = utils.get_message(transport)

    print('Ответ сервера: ', response)
    print(utils.parse_response(response))


if __name__ == '__main__':
    main()