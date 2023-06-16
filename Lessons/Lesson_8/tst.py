import os, sys, json, time, threading
from socket import socket, AF_INET, SOCK_STREAM
from dotenv import load_dotenv
from datetime import datetime 
import logging
import log.client_log_config
from log.decor_log import log
from utils import send_message, get_message, create_presence_message, parse_response


# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')

@log
def message_from_server(sock, my_username):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    while True:
        try:
            message = get_message(sock)
            if os.getenv('ACTION') in message and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
                    and os.getenv('SENDER') in message and os.getenv('DESTINATION') in message \
                    and os.getenv('MESSAGE_TEXT') in message and message[os.getenv('DESTINATION')] == my_username:
                print(f"\nПолучено сообщение от пользователя {message[os.getenv('SENDER')]} "
                      f"[{datetime.now().strftime('%Y-%m-%d %H.%M.%S')}]:"
                      f"\n{message[os.getenv('MESSAGE_TEXT')]}")
                CLIENT_LOGGER.info(f"Получено сообщение от пользователя {message[os.getenv('SENDER')]}:"
                            f"\n{message[os.getenv('MESSAGE_TEXT')]}")
            else:
                CLIENT_LOGGER.error(f"Получено некорректное сообщение с сервера: {message}")
        except (OSError, ConnectionError, ConnectionAbortedError,
                ConnectionResetError, json.JSONDecodeError):
            CLIENT_LOGGER.critical(f"Потеряно соединение с сервером.")
            break


@log
def create_message(sock, username='Guest'):
    """
    Функция запрашивает кому отправить сообщение и само сообщение,
    и отправляет полученные данные на сервер
    :param sock:
    :param account_name:
    :return:
    """
    to_user = input(f"[{username}] Введите получателя сообщения: ")
    message = input(f"[{username}] Введите сообщение для отправки: ")
    message_dict = {
        os.getenv('ACTION'): os.getenv('MESSAGE'),
        os.getenv('SENDER'): username,
        os.getenv('DESTINATION'): to_user,
        os.getenv('TIME'): time.time(),
        os.getenv('MESSAGE_TEXT'): message
    }
    CLIENT_LOGGER.debug(f"Сформирован словарь сообщения: {message_dict}")
    try:
        send_message(sock, message_dict)
        CLIENT_LOGGER.info(f"Отправлено сообщение для пользователя {to_user}")
    except:
        CLIENT_LOGGER.critical("Потеряно соединение с сервером.")
        sys.exit(1)


def print_help():
    """Функция выводящяя справку по использованию"""
    print('Поддерживаемые команды:')
    print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
    print('help - вывести подсказки по командам')
    print('exit - выход из программы')


@log
def create_exit_message(account_name):
    """Функция создаёт словарь с сообщением о выходе"""
    return {
        os.getenv('ACTION'): os.getenv('EXIT'),
        os.getenv('TIME'): time.time(),
        os.getenv('ACCOUNT_NAME'): account_name
    }

@log
def user_interactive(sock, username):
    """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
    print_help()
    while True:
        user_command = input(f"[{username}] Введите команду: ")
        if user_command == 'message':
            create_message(sock, username)
        elif user_command == 'help':
            print_help()
        elif user_command == 'exit':
            send_message(sock, create_exit_message(username))
            print('Завершение соединения.')
            CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
            # Задержка неоходима, чтобы успело уйти сообщение о выходе
            time.sleep(0.5)
            break
        else:
            print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


def client():
    load_dotenv()
    """Сообщаем о запуске"""
    print('Консольный месседжер. Клиентский модуль.')

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

    # необходимо запросить пользователя.
    # client_name = input('Введите имя пользователя: ')
    # CLIENT_LOGGER.info(
    #     f'Запущен клиент с параметрами: адрес сервера: {serv_addr}, '
    #     f'порт: {serv_port}, имя пользователя: {client_name}')
        
        # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((serv_addr, int(serv_port)))
        client_name = input('Введите имя пользователя: ')
        send_message(s, create_presence_message(client_name))
        answer = parse_response(get_message(s))
        CLIENT_LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером: {answer}')
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(
            f'Не удалось подключиться к серверу {serv_addr}:{serv_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
        # Если соединение с сервером установлено корректно,
        # запускаем клиенский процесс приёма сообщний
        receiver = threading.Thread(target=message_from_server, args=(s, client_name))
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=user_interactive, args=(s, client_name))
        user_interface.daemon = True
        user_interface.start()
        CLIENT_LOGGER.debug('Клиентские процессы загружены')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break
   

if __name__ == '__main__':
    client()