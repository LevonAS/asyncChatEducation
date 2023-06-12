import os, sys, json, time
from socket import socket, AF_INET, SOCK_STREAM
from dotenv import load_dotenv
import logging
import log.client_log_config
from log.decor_log import log
from utils import create_presence_message, send_message, get_message, parse_response


# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')

@log
def message_from_server(message):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    # print("CL_MFS_1", message, "||||")
    if os.getenv('ACTION') in message \
            and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
            and os.getenv('SENDER') in message \
            and os.getenv('MESSAGE_TEXT') in message:
        # print("CL_MFS_2", message, "||||")
        print(f"Получено сообщение от пользователя {message[os.getenv('SENDER')]}:\n"
              f"  {message[os.getenv('MESSAGE_TEXT')]}")
        CLIENT_LOGGER.info(f'Получено сообщение от пользователя '
                    f"{message[os.getenv('SENDER')]}:\n{message[os.getenv('MESSAGE_TEXT')]}")
    else:
        CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')


@log
def create_message(sock, account_name='Guest'):
    """Функция запрашивает текст сообщения и возвращает его.
    Так же завершает работу при вводе подобной комманды
    """
    message = input('Введите сообщение для отправки или \'!!!\' для завершения работы: ')
    if message == '!!!':
        sock.close()
        CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
        print('Спасибо за использование нашего сервиса!')
        sys.exit(0)
    message_dict = {
        os.getenv('ACTION'): os.getenv('MESSAGE'),
        os.getenv('TIME'): time.time(),
        os.getenv('ACCOUNT_NAME'): account_name,
        os.getenv('MESSAGE_TEXT'): message
    }
    CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
    return message_dict


def client():
    load_dotenv()

    global serv_addr, serv_port

    try:
        if sys.argv[1] and sys.argv[2]:
            serv_addr, serv_port = sys.argv[1], sys.argv[2]
            if int(serv_port) < 1024 or int(serv_port) > 65535:
                raise ValueError
    except IndexError:
        serv_addr, serv_port = os.getenv(
            'DEFAULT_IP_ADDRESS'), os.getenv('DEFAULT_PORT')
    except ValueError:
        CLIENT_LOGGER.critical(
            'В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

        # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((serv_addr, int(serv_port)))
        send_message(s, create_presence_message('Guest'))
        answer = parse_response(get_message(s))
        CLIENT_LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(
            f'Не удалось подключиться к серверу {serv_addr}:{serv_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
   
        working_mode = input('Нажмите "1" для перехода в режим приёма сообщений, либо\n'
                    'нажмите "2" для перехода в режим отправки сообщений, либо\n'
                    'нажмите "q" - выход из терминала:\n')
        
        
        while True:
            if working_mode == 'q':
                exit()
            
            elif working_mode == '1':
                print('Режим работы - приём сообщений.')
                try:

                    message_from_server(get_message(s))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
                    sys.exit(1)

            elif working_mode == '2':
                print('Режим работы - отправка сообщений.')
                # режим работы - отправка сообщений
                try:
                    send_message(s, create_message(s))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
                    sys.exit(1)


if __name__ == '__main__':
    client()