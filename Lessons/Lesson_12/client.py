import os, sys, json, time, threading, argparse, socket
from dotenv import load_dotenv
from datetime import datetime 
import logging
import log.client_log_config
from log.decor_log import log

from client_database import ClientDatabase
from utils import ClientVerifier
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError

# Объект блокировки сокета и работы с базой данных
sock_lock = threading.Lock()
database_lock = threading.Lock()

CLIENT_LOGGER = logging.getLogger('client')


# Класс формировки и отправки сообщений на сервер и взаимодействия с пользователем.
class ClientSender(threading.Thread):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()


    def create_exit_message(self):
        """Метод создаёт словарь с сообщением о выходе"""
        return {
            os.getenv('ACTION'): os.getenv('EXIT'),
            os.getenv('TIME'): time.time(),
            os.getenv('ACCOUNT_NAME'): self.account_name
        }

    @log
    def get_active_users(self, sock, username='Guest'):
        """Метод генерирует запрос получение списка пользователей подключённых к серверу"""
        message_dict = {
            os.getenv('ACTION'): os.getenv('GETULIST'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): username,
        }
        CLIENT_LOGGER.debug(f"Сформирован словарь сообщения: {message_dict}")
        try:
            send_message(sock, message_dict)
            CLIENT_LOGGER.info(f"Отправлен запрос на получение списка пользователей подключённых к серверу ")
        except:
            CLIENT_LOGGER.critical("Потеряно соединение с сервером.")
            sys.exit(1)
    
    # Функция запрашивает кому отправить сообщение и само сообщение, и отправляет полученные данные на сервер.
    def create_message(self):
        """
        Метод запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер
        """
        to = input(f"[{self.account_name}] Введите получателя сообщения: ")
        message = input(f"[{self.account_name}] Введите сообщение для отправки: ")

        # Проверим, что получатель существует
        with database_lock:
            if not self.database.check_user(to):
                CLIENT_LOGGER.error(f'Попытка отправить сообщение незарегистрированому получателю: {to}')
                return

        message_dict = {
            os.getenv('ACTION'): os.getenv('MESSAGE'),
            os.getenv('SENDER'): self.account_name,
            os.getenv('DESTINATION'): to,
            os.getenv('TIME'): time.time(),
            os.getenv('MESSAGE_TEXT'): message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Сохраняем сообщения для истории
        with database_lock:
            self.database.save_message(self.account_name , to , message)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to}')
            except OSError as err:
                if err.errno:
                    CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    CLIENT_LOGGER.error('Не удалось передать сообщение. Таймаут соединения')

    # Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
    def run(self):
        self.print_help()
        while True:
            command = input(f"[{self.account_name}] Введите команду: ")
            # Если отправка сообщения - соответствующий метод
            if command == 'message':
                self.create_message()

            # Вывод помощи
            elif command == 'help':
                self.print_help()

            # Выход. Отправляем сообщение серверу о выходе.
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except:
                        pass
                    print('Завершение соединения.')
                    CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            # Вывести список пользователей подключённых к серверу
            elif command == 'users':
                self.get_active_users(self.sock, self.account_name)
            
            # Список контактов
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()

            # история сообщений.
            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    # Функция выводящяя справку по использованию.
    def print_help(self):
        print('Поддерживаемые команды:')
        print('users - вывести список пользователей подключённых к серверу')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print(f'exit - выход из программы\n')

    # Функция выводящяя историю сообщений
    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    # Функция изменеия контактов
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    CLIENT_LOGGER.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock , self.account_name, edit)
                    except ServerError:
                        CLIENT_LOGGER.error('Не удалось отправить информацию на сервер.')


# Класс-приёмник сообщений с сервера. Принимает сообщения, выводит в консоль , сохраняет в базу.
class ClientReader(threading.Thread):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    # Основной цикл приёмника сообщений, принимает сообщения, выводит в консоль. Завершается при потере соединения.
    def run(self):
        while True:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)

                # Принято некорректное сообщение
                except IncorrectDataRecivedError:
                    CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    if err.errno:
                        CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                        break
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                    break
                # Если пакет корретно получен выводим в консоль и записываем в базу.
                else:
                    if os.getenv('ACTION') in message \
                            and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
                            and os.getenv('SENDER') in message \
                            and os.getenv('DESTINATION') in message \
                            and os.getenv('MESSAGE_TEXT') in message \
                            and message[os.getenv('DESTINATION')] == self.account_name:
                        print(f"\nПолучено сообщение от пользователя {message[os.getenv('SENDER')]}:\n{message[os.getenv('MESSAGE_TEXT')]}")
                        # Захватываем работу с базой данных и сохраняем в неё сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[os.getenv('SENDER')], self.account_name, message[os.getenv('MESSAGE_TEXT')])
                            except:
                                CLIENT_LOGGER.error('Ошибка взаимодействия с базой данных')

                        CLIENT_LOGGER.info(f"Получено сообщение от пользователя {message[os.getenv('SENDER')]}:\n{message[os.getenv('MESSAGE_TEXT')]}")
                    
                    elif os.getenv('ACTION') in message and message[os.getenv('ACTION')] == os.getenv('GETULIST') \
                        and os.getenv('USERS_LIST') in message:
                        print(f"Список пользователей подключённых к серверу: "
                              f"  \n{message[os.getenv('USERS_LIST')]}")
                    
                    else:
                        CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')

"""
##########################################################################
"""
@log
def create_presence_message(account_name):
    """Метод генерирует запрос о присутствии клиента"""
    message = {
        os.getenv('ACTION'): os.getenv('PRESENCE'),
        os.getenv('TIME'): time.time(),
        os.getenv('USER'): {
            os.getenv('ACCOUNT_NAME'): account_name
        }
    }
    CLIENT_LOGGER.debug(f"Сформировано {os.getenv('PRESENCE')} сообщение для пользователя {account_name}")
    # self.CLIENT_LOGGER.debug(f"Сформировано {os.getenv('PRESENCE')} сообщение для пользователя {account_name}")
    return message

@log
def parse_response(message):
    """
    Метод разбирает ответ сервера на сообщение о присутствии,
    возращает 200 если все ОК или генерирует исключение при ошибке
    """
    # self.CLIENT_LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if os.getenv('RESPONSE') in message:
        # print("/\/CLN_pr_1", "RESPONSE:", message[os.getenv('RESPONSE')])
        if message[os.getenv('RESPONSE')] == 200:           
            return 200
        elif message[os.getenv('RESPONSE')] == 400:
            raise ServerError(f"400 : {message[os.getenv('ERROR')]}")
    raise ReqFieldMissingError(os.getenv('RESPONSE'))

@log
def send_message(open_socket, message):
    json_message = json.dumps(message)
    response = json_message.encode(os.getenv('ENCODING'))
    open_socket.send(response)
    # print("CLN_SM_1", "[message:]", message, "\n[response:]", response, "\n[open_socket:]", open_socket, "\n")

@log
def get_message(client):
    """
    Утилита приёма и декодирования сообщения принимает байты выдаёт словарь,
    если приняточто-то другое отдаёт ошибку значения
    """
    response = client.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
    # print("///CLN_GM_1", response, "||||")
    if isinstance(response, bytes):
        json_response = response.decode(os.getenv('ENCODING'))
        response_dict = json.loads(json_response)
        if isinstance(response_dict, dict):
            # print("///CLN_GM_2", response_dict, "||||")
            return response_dict
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError


# Функция запрос контакт листа
def contacts_list_request(sock, name):
    CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        os.getenv('ACTION'): os.getenv('GET_CONTACTS'),
        os.getenv('TIME'): time.time(),
        os.getenv('USER'): name
    }
    CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    CLIENT_LOGGER.debug(f'Получен ответ {ans}')
    if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 202:
        return ans[os.getenv('LIST_INFO')]
    else:
        raise ServerError


# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    CLIENT_LOGGER.debug(f'Создание контакта {contact}')
    req = {
        os.getenv('ACTION'): os.getenv('ADD_CONTACT'),
        os.getenv('TIME'): time.time(),
        os.getenv('USER'): username,
        os.getenv('ACCOUNT_NAME'): contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    # print("///CLN_main_2", username)
    CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {username}')
    req = {
        os.getenv('ACTION'): os.getenv('USERS_REQUEST'),
        os.getenv('TIME'): time.time(),
        os.getenv('ACCOUNT_NAME'): username
    }
    send_message(sock, req)
    # print("///CLN_main_3", username)
    ans = get_message(sock)
    # print("///CLN_main_4", ans)
    if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 202:
        return ans[os.getenv('LIST_INFO')]
    else:
        raise ServerError


# Функция удаления пользователя из контакт листа
def remove_contact(sock, username, contact):
    CLIENT_LOGGER.debug(f'Создание контакта {contact}')
    req = {
        os.getenv('ACTION'): os.getenv('REMOVE_CONTACT'),
        os.getenv('TIME'): time.time(),
        os.getenv('USER'): username,
        os.getenv('ACCOUNT_NAME'): contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


# Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера.
def database_load(sock, database, username):
    # Загружаем список известных пользователей
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        CLIENT_LOGGER.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)
    # print("///CLN_main_7", username)
    # Загружаем список контактов
    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def connect_to_server(sock, client_name):
    # global client_name
    # client_name = ""
    try:
        if not client_name:
            client_name = input('Введите имя пользователя: ')
        send_message(sock, create_presence_message(client_name))
        answer = parse_response(get_message(sock))
        if answer == 200:
            CLIENT_LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
            print(f'Установлено соединение с сервером.')
            return client_name
        elif answer == 409:
            print(f' Пользователь {client_name} уже подключён к серверу. '
                f'Попробуте подключиться с другим именем.')
            sys.exit(1)
            # connect_to_server(sock)
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(
            f'Не удалось подключиться к серверу {serv_addr}:{dest_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    


@log
def client_args_parser():
    """ Парсер аргументов коммандной строки """
    parser = argparse.ArgumentParser(description='Client script')
    parser.add_argument('addr', default=os.getenv('DEFAULT_IP_ADDRESS'), type=str, nargs='?', \
        help="Параметр 'addr' позволяет указать IP-адрес, с которого будут приниматься соединения. (по умолчанию адрес не указан, ")
    parser.add_argument('port', default=os.getenv('DEFAULT_PORT'), type=int, nargs='?', \
        help="Параметр 'port' позволяет указать порт сервера (по умолчанию 7777)")
    parser.add_argument('-n', '--name', default=None, nargs='?', \
        help="Параметр '-n' позволяет указать имя пользователя при запуске")
    
    args = parser.parse_args(sys.argv[1:])
    serv_addr = args.addr
    serv_port = args.port
    client_name = args.name

    # проверим подходящий номер порта
    if not 1023 < serv_port < 65536:
        CLIENT_LOGGER.critical(f"Попытка запуска клиента с неподходящим номером порта удалённого сервера: {serv_port}. "
            f"Допустимы адреса с 1024 до 65535. Клиенту будет принудительно установлен порт подключения к удалённому серверу по умолчанию : {os.getenv('DEFAULT_PORT')}")
        serv_port = os.getenv('DEFAULT_PORT')
    
    return serv_addr, serv_port, client_name 


def main():
    load_dotenv()
    # client_name = ""
    
    # Сообщаем о запуске
    print('Консольный месседжер. Клиентский модуль.')

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = client_args_parser()

    CLIENT_LOGGER.info(f'Запущен клиент с параметрами, адрес сервера: {server_address}, '
            f'порт сервера: {server_port}')

    # Инициализация сокета и сообщение серверу о нашем появлении
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Таймаут 1 секунда, необходим для освобождения сокета.
    s.settimeout(1)
    s.connect((server_address, server_port))
    
    # Установка соединения с сервером
    client = connect_to_server(s, client_name)

    
    # Инициализация БД
    database = ClientDatabase(client)
    # print("///CLN_main_1", client)
    database_load(s, database, client)
    # print("///CLN_main_6", client)

    # Если соединение с сервером установлено корректно, запускаем поток взаимодействия с пользователем
    module_sender = ClientSender(client, s, database)
    module_sender.daemon = True
    module_sender.start()
    CLIENT_LOGGER.debug('Запущены процессы')
    # print("///CLN_main_7", client)

    # затем запускаем поток - приёмник сообщений.
    module_receiver = ClientReader(client, s, database)
    module_receiver.daemon = True
    module_receiver.start()
    # print("///CLN_main_8", client)

    # Watchdog основной цикл, если один из потоков завершён, то значит или потеряно соединение или пользователь
    # ввёл exit. Поскольку все события обработываются в потоках, достаточно просто завершить цикл.
    while True:
        time.sleep(1)
        if module_receiver.is_alive() and module_sender.is_alive():
            continue
        break


if __name__ == '__main__':
    main()

