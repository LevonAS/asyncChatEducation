import os, sys, json, time, threading
from socket import socket, AF_INET, SOCK_STREAM
from dotenv import load_dotenv
from datetime import datetime 
import logging
import log.client_log_config
from log.decor_log import log
# from utils import send_message, get_message
# from utils import Utils


class Client():
    # utils = Utils()

    def __init__(self):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.CLIENT_LOGGER = logging.getLogger('client')

        self.run()

    @log
    def send_message(self, open_socket, message):
        json_message = json.dumps(message)
        response = json_message.encode(os.getenv('ENCODING'))
        open_socket.send(response)
        # print("CLN_SM_1", "[message:]", message, "\n[response:]", response, "\n[open_socket:]", open_socket, "\n")

    @log
    def get_message(self, client):
        """
        Утилита приёма и декодирования сообщения принимает байты выдаёт словарь,
        если приняточто-то другое отдаёт ошибку значения
        :param client:
        :return:
        """
        response = client.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
        # print("CLN_GM_1", response, "||||")
        if isinstance(response, bytes):
            json_response = response.decode(os.getenv('ENCODING'))
            response_dict = json.loads(json_response)
            if isinstance(response_dict, dict):
                # print("CLN_GM_2", response_dict, "||||")
                return response_dict
            raise ValueError
        raise ValueError


    @log
    def create_presence_message(self, account_name):
        """Метод генерирует запрос о присутствии клиента"""
        message = {
            os.getenv('ACTION'): os.getenv('PRESENCE'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): {
                os.getenv('ACCOUNT_NAME'): account_name
            }
        }
        # self.CLIENT_LOGGER.debug(f"Сформировано {os.getenv('PRESENCE')} сообщение для пользователя {account_name}")
        return message


    @log
    def parse_response(self, message):
        """
        Метод разбирает ответ сервера на сообщение о присутствии,
        возращает 200 если все ОК или генерирует исключение при ошибке
        """
        # self.CLIENT_LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
        if os.getenv('RESPONSE') in message:
            if message[os.getenv('RESPONSE')] == 200:
                return 200
            elif message[os.getenv('RESPONSE')] == 409:
                return 409
            return 400
        raise ValueError


    @log
    def message_from_server(self, sock, my_username):
        """Метод - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            try:
                message = self.get_message(sock)
                if os.getenv('ACTION') in message and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
                        and os.getenv('SENDER') in message and os.getenv('DESTINATION') in message \
                        and os.getenv('MESSAGE_TEXT') in message \
                        and message[os.getenv('DESTINATION')] == my_username:
                    print(f"\nПолучено сообщение от пользователя {message[os.getenv('SENDER')]} "
                        f"[{datetime.now().strftime('%Y-%m-%d %H.%M.%S')}]:"
                        f"\n{message[os.getenv('MESSAGE_TEXT')]}")
                    self.CLIENT_LOGGER.info(f"  Получено сообщение от пользователя {message[os.getenv('SENDER')]}:"
                                f"\n{message[os.getenv('MESSAGE_TEXT')]}")
                elif os.getenv('ACTION') in message and message[os.getenv('ACTION')] == os.getenv('GETULIST') \
                        and os.getenv('USERS_LIST') in message:
                    print(f"Список пользователей подключённых к серверу: "
                        f"  \n{message[os.getenv('USERS_LIST')]}")
                else:
                    self.CLIENT_LOGGER.error(f"Получено некорректное сообщение с сервера: {message}")
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                self.CLIENT_LOGGER.critical(f"Потеряно соединение с сервером.")
                break


    @log
    def create_message(self, sock, username='Guest'):
        """
        Метод запрашивает кому отправить сообщение и само сообщение,
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
        self.CLIENT_LOGGER.debug(f"Сформирован словарь сообщения: {message_dict}")
        try:
            self.send_message(sock, message_dict)
            self.CLIENT_LOGGER.info(f"Отправлено сообщение для пользователя {to_user}")
        except:
            self.CLIENT_LOGGER.critical("Потеряно соединение с сервером.")
            sys.exit(1)


    def print_help(self):
        """Метод выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('  message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('  users - вывести список пользователей подключённых к серверу')
        print('  help - вывести подсказки по командам')
        print('  exit - выход из программы')


    @log
    def create_exit_message(self, account_name):
        """Метод создаёт словарь с сообщением о выходе"""
        return {
            os.getenv('ACTION'): os.getenv('EXIT'),
            os.getenv('TIME'): time.time(),
            os.getenv('ACCOUNT_NAME'): account_name
        }

    @log
    def get_active_users(self, sock, username='Guest'):
        """Метод генерирует запрос получение списка пользователей подключённых к серверу"""
        message_dict = {
            os.getenv('ACTION'): os.getenv('GETULIST'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): username,
        }
        self.CLIENT_LOGGER.debug(f"Сформирован словарь сообщения: {message_dict}")
        try:
            self.send_message(sock, message_dict)
            self.CLIENT_LOGGER.info(f"Отправлен запрос на получение списка пользователей подключённых к серверу ")
        except:
            self.CLIENT_LOGGER.critical("Потеряно соединение с сервером.")
            sys.exit(1)


    @log
    def user_interactive(self, sock, username):
        """Метод взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
        self.print_help()
        while True:
            time.sleep(1)
            user_command = input(f"[{username}] Введите команду: ")
            if user_command == 'message':
                self.create_message(sock, username)
            elif user_command == 'users':
                self.get_active_users(sock, username)
            elif user_command == 'help':
                self.print_help()
            elif user_command == 'exit':
                self.send_message(sock, self.create_exit_message(username))
                print('Завершение соединения.')
                self.CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


    def connect_to_server(self, sock):
        try:
            user_name = input('Введите имя пользователя: ')
            self.send_message(sock, self.create_presence_message(user_name))
            answer = self.parse_response(self.get_message(sock))
            if answer == 200:
                self.CLIENT_LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
                print(f'Установлено соединение с сервером.')
                return user_name
            elif answer == 409:
                print(f' Пользователь {user_name} уже подключён к серверу. '
                    f'Попробуте подключиться с другим именем.')
                sys.exit(1)
                # connect_to_server(sock)
        except json.JSONDecodeError:
            self.CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except ConnectionRefusedError:
            self.CLIENT_LOGGER.critical(
                f'Не удалось подключиться к серверу {serv_addr}:{serv_port}, '
                f'конечный компьютер отверг запрос на подключение.')
            sys.exit(1)


    def start_client(self):
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
            self.CLIENT_LOGGER.critical(
                'В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
            sys.exit(1)

            
        # Инициализация сокета 
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.connect((serv_addr, int(serv_port)))
        self.client_name = self.connect_to_server(self.s)

        # Если соединение с сервером установлено корректно,
        # запускаем клиенский процесс приёма сообщний
        receiver = threading.Thread(target=self.message_from_server, args=(self.s, self.client_name))
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=self.user_interactive, args=(self.s, self.client_name))
        user_interface.daemon = True
        user_interface.start()
        self.CLIENT_LOGGER.debug('Клиентские процессы загружены')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break
   
    def run(self):
        self.start_client()


if __name__ == '__main__':
    client = Client()