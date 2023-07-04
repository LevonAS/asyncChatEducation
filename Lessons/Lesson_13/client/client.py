import os, sys, json, time, threading, argparse, socket
from dotenv import load_dotenv
from datetime import datetime 
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject
import logging
# sys.path.append('..')
project_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_directory)

import log.client_log_config
from log.decor_log import go, log

from client_database import ClientDatabase
from utils import ClientVerifier
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from start_dialog import UserNameDialog
from client_database import ClientDatabase
from main_window import ClientMainWindow


# database_lock = threading.Lock()

CLIENT_LOGGER = logging.getLogger('client')
socket_lock = threading.Lock()


# Класс - Client-Транспорт, отвечает за взаимодействие с сервером
class Client(threading.Thread, QObject):
    # Сигналы новое сообщение и потеря соединения
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        # Вызываем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        # Класс База данных - работа с базой
        self.database = database
        # Имя пользователя
        self.username = username
        # Сокет для работы с сервером
        self.s = None
        # Устанавливаем соединение:
        self.connection_init(port, ip_address)
        # Обновляем таблицы известных пользователей и контактов
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            CLIENT_LOGGER.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            # Флаг продолжения работы транспорта.
        self.running = True

    # Функция инициализации соединения с сервером
    def connection_init(self, port, ip):
        # Инициализация сокета и сообщение серверу о нашем появлении
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут необходим для освобождения сокета.
        self.s.settimeout(5)
        print("///CLN_c1_1", port, ip)

        # Соединяемся, 5 попыток соединения, флаг успеха ставим в True если удалось
        connected = False
        for i in range(5):
            CLIENT_LOGGER.info(f'Попытка подключения №{i + 1}')
            try:
                self.s.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        # Если соединится не удалось - исключение
        if not connected:
            CLIENT_LOGGER.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        CLIENT_LOGGER.debug('Установлено соединение с сервером')

        # Посылаем серверу приветственное сообщение и получаем ответ что всё нормально или ловим исключение.
        try:
            with socket_lock:
                send_message(self.s, self.create_presence())
                self.process_server_ans(get_message(self.s))
        except (OSError, json.JSONDecodeError):
            CLIENT_LOGGER.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')

        # Раз всё хорошо, сообщение о установке соединения.
        CLIENT_LOGGER.info('Соединение с сервером успешно установлено.')

    # Функция, генерирующая приветственное сообщение для сервера
    def create_presence(self):
        """Метод генерирует запрос о присутствии клиента"""
        message = {
            os.getenv('ACTION'): os.getenv('PRESENCE'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): {
                os.getenv('ACCOUNT_NAME'): self.username
            }
        }
        CLIENT_LOGGER.debug(f"Сформировано {os.getenv('PRESENCE')} сообщение для пользователя {self.username}")
        return message

    # Функция обрабатывающяя сообщения от сервера. Ничего не возращает. Генерирует исключение при ошибке.
    def process_server_ans(self, message):
        CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')
        print("/\/CLN_psa_1", "message:", message)

        # Если это подтверждение чего-либо
        if os.getenv('RESPONSE') in message:
            if message[os.getenv('RESPONSE')] == 200:
                return
            elif message[os.getenv('RESPONSE')] == 400:
                raise ServerError(f"{message[os.getenv('ERROR')]}")
            else:
                CLIENT_LOGGER.debug(f"Принят неизвестный код подтверждения {message[os.getenv('RESPONSE')]}")

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о новом сообщении
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
                and os.getenv('SENDER') in message \
                and os.getenv('DESTINATION') in message \
                and os.getenv('MESSAGE_TEXT') in message \
                and message[os.getenv('DESTINATION')] == self.username:
            print("/\/CLN_psa_2", "message:", message[os.getenv('MESSAGE_TEXT')])
            CLIENT_LOGGER.debug(f"Получено сообщение от пользователя {message[os.getenv('SENDER')]}:{message[os.getenv('MESSAGE_TEXT')]}")
            self.database.save_message(message[os.getenv('SENDER')] , 'in' , message[os.getenv('MESSAGE_TEXT')])
            self.new_message.emit(message[os.getenv('SENDER')])
            print("/\/CLN_psa_3", "message:", message[os.getenv('MESSAGE_TEXT')])


    # Функция обновляющая контакт - лист с сервера
    def contacts_list_update(self):
        CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователся {self.username}')
        req = {
            os.getenv('ACTION'): os.getenv('GET_CONTACTS'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): self.username
        }
        CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        CLIENT_LOGGER.debug(f'Получен ответ {ans}')
        if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 202:
            for contact in ans[os.getenv('LIST_INFO')]:
                self.database.add_contact(contact)
        else:
            CLIENT_LOGGER.error('Не удалось обновить список контактов.')

    # Функция обновления таблицы известных пользователей.
    def user_list_update(self):
        print("///CLN_ulu_1", self.username)
        CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            os.getenv('ACTION'): os.getenv('USERS_REQUEST'),
            os.getenv('TIME'): time.time(),
            os.getenv('ACCOUNT_NAME'): self.username
        }
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 202:
            self.database.add_users(ans[os.getenv('LIST_INFO')])
        else:
            CLIENT_LOGGER.error('Не удалось обновить список известных пользователей.')

    # Функция сообщающая на сервер о добавлении нового контакта
    def add_contact(self, contact):
        CLIENT_LOGGER.debug(f'Создание контакта {contact}')
        req = {
            os.getenv('ACTION'): os.getenv('ADD_CONTACT'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): self.username,
            os.getenv('ACCOUNT_NAME'): contact
        }
        with socket_lock:
            send_message(self.s, req)
            self.process_server_ans(get_message(self.s))

    # Функция удаления клиента на сервере
    def remove_contact(self, contact):
        CLIENT_LOGGER.debug(f'Удаление контакта {contact}')
        req = {
            os.getenv('ACTION'): os.getenv('REMOVE_CONTACT'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): self.username,
            os.getenv('ACCOUNT_NAME'): contact
        }
        with socket_lock:
            send_message(self.s, req)
            self.process_server_ans(get_message(self.s))

    # Функция закрытия соединения, отправляет сообщение о выходе.
    def transport_shutdown(self):
        self.running = False
        message = {
            os.getenv('ACTION'): os.getenv('EXIT'),
            os.getenv('TIME'): time.time(),
            os.getenv('ACCOUNT_NAME'): self.username
        }
        with socket_lock:
            try:
                send_message(self.s, message)
            except OSError:
                pass
        CLIENT_LOGGER.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    # Функция отправки сообщения на сервер
    def send_message(self, to, message):
        message_dict = {
            os.getenv('ACTION'): os.getenv('MESSAGE'),
            os.getenv('SENDER'): self.username,
            os.getenv('DESTINATION'): to,
            os.getenv('TIME'): time.time(),
            os.getenv('MESSAGE_TEXT'): message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_message(self.s, message_dict)
            self.process_server_ans(get_message(self.s))
            CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        CLIENT_LOGGER.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то отправка может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with socket_lock:
                try:
                    self.s.settimeout(0.5)
                    message = get_message(self.s)
                except OSError as err:
                    if err.errno:
                        CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    CLIENT_LOGGER.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    CLIENT_LOGGER.debug(f'Принято сообщение с сервера: {message}')
                    print("/\/CLN_run_1", "message:", message)
                    self.process_server_ans(message)
                finally:
                    self.s.settimeout(5)


"""
##########################################################################
"""

@log
def send_message(open_socket, message):
    json_message = json.dumps(message)
    response = json_message.encode(os.getenv('ENCODING'))
    open_socket.send(response)
    print("CLN_SM_1", "[message:]", message, "\n[response:]", response, "\n[open_socket:]", open_socket, "\n")

@log
def get_message(client):
    """
    Утилита приёма и декодирования сообщения принимает байты выдаёт словарь,
    если приняточто-то другое отдаёт ошибку значения
    """
    response = client.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
    print("///CLN_GM_1", response, "||||")
    if isinstance(response, bytes):
        json_response = response.decode(os.getenv('ENCODING'))
        response_dict = json.loads(json_response)
        if isinstance(response_dict, dict):
            print("///CLN_GM_2", response_dict, "||||")
            return response_dict
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError

        
#@log
# def create_presence_message(account_name):
#     """Метод генерирует запрос о присутствии клиента"""
#     message = {
#         os.getenv('ACTION'): os.getenv('PRESENCE'),
#         os.getenv('TIME'): time.time(),
#         os.getenv('USER'): {
#             os.getenv('ACCOUNT_NAME'): account_name
#         }
#     }
#     # CLIENT_LOGGER.debug(f"Сформировано {os.getenv('PRESENCE')} сообщение для пользователя {account_name}")
#     # self.CLIENT_LOGGER.debug(f"Сформировано {os.getenv('PRESENCE')} сообщение для пользователя {account_name}")
#     return message

#@log
# def parse_response(message):
#     """
#     Метод разбирает ответ сервера на сообщение о присутствии,
#     возращает 200 если все ОК или генерирует исключение при ошибке
#     """
#     # self.CLIENT_LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
#     if os.getenv('RESPONSE') in message:
#         # print("/\/CLN_pr_1", "RESPONSE:", message[os.getenv('RESPONSE')])
#         if message[os.getenv('RESPONSE')] == 200:           
#             return 200
#         elif message[os.getenv('RESPONSE')] == 400:
#             raise ServerError(f"400 : {message[os.getenv('ERROR')]}")
#     raise ReqFieldMissingError(os.getenv('RESPONSE'))


# # Функция запрос контакт листа
# def contacts_list_request(sock, name):
#     CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователся {name}')
#     req = {
#         os.getenv('ACTION'): os.getenv('GET_CONTACTS'),
#         os.getenv('TIME'): time.time(),
#         os.getenv('USER'): name
#     }
#     CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
#     send_message(sock, req)
#     ans = get_message(sock)
#     CLIENT_LOGGER.debug(f'Получен ответ {ans}')
#     if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 202:
#         return ans[os.getenv('LIST_INFO')]
#     else:
#         raise ServerError


# # Функция добавления пользователя в контакт лист
# def add_contact(sock, username, contact):
#     CLIENT_LOGGER.debug(f'Создание контакта {contact}')
#     req = {
#         os.getenv('ACTION'): os.getenv('ADD_CONTACT'),
#         os.getenv('TIME'): time.time(),
#         os.getenv('USER'): username,
#         os.getenv('ACCOUNT_NAME'): contact
#     }
#     send_message(sock, req)
#     ans = get_message(sock)
#     if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 200:
#         pass
#     else:
#         raise ServerError('Ошибка создания контакта')
#     print('Удачное создание контакта.')


# # Функция запроса списка известных пользователей
# def user_list_request(sock, username):
#     # print("///CLN_main_2", username)
#     CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {username}')
#     req = {
#         os.getenv('ACTION'): os.getenv('USERS_REQUEST'),
#         os.getenv('TIME'): time.time(),
#         os.getenv('ACCOUNT_NAME'): username
#     }
#     send_message(sock, req)
#     # print("///CLN_main_3", username)
#     ans = get_message(sock)
#     # print("///CLN_main_4", ans)
#     if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 202:
#         return ans[os.getenv('LIST_INFO')]
#     else:
#         raise ServerError


# # Функция удаления пользователя из контакт листа
# def remove_contact(sock, username, contact):
#     CLIENT_LOGGER.debug(f'Создание контакта {contact}')
#     req = {
#         os.getenv('ACTION'): os.getenv('REMOVE_CONTACT'),
#         os.getenv('TIME'): time.time(),
#         os.getenv('USER'): username,
#         os.getenv('ACCOUNT_NAME'): contact
#     }
#     send_message(sock, req)
#     ans = get_message(sock)
#     if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 200:
#         pass
#     else:
#         raise ServerError('Ошибка удаления клиента')
#     print('Удачное удаление')


# # Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера.
# def database_load(sock, database, username):
#     # Загружаем список известных пользователей
#     try:
#         users_list = user_list_request(sock, username)
#     except ServerError:
#         CLIENT_LOGGER.error('Ошибка запроса списка известных пользователей.')
#     else:
#         database.add_users(users_list)
#     # print("///CLN_main_7", username)
#     # Загружаем список контактов
#     try:
#         contacts_list = contacts_list_request(sock, username)
#     except ServerError:
#         CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
#     else:
#         for contact in contacts_list:
#             database.add_contact(contact)


# def connect_to_server(sock, client_name):
#     # global client_name
#     # client_name = ""
#     try:
#         if not client_name:
#             client_name = input('Введите имя пользователя: ')
#         send_message(sock, create_presence_message(client_name))
#         answer = parse_response(get_message(sock))
#         if answer == 200:
#             CLIENT_LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
#             print(f'Установлено соединение с сервером.')
#             return client_name
#         elif answer == 409:
#             print(f' Пользователь {client_name} уже подключён к серверу. '
#                 f'Попробуте подключиться с другим именем.')
#             sys.exit(1)
#             # connect_to_server(sock)
#     except json.JSONDecodeError:
#         CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
#         sys.exit(1)
#     except ConnectionRefusedError:
#         CLIENT_LOGGER.critical(
#             f'Не удалось подключиться к серверу {serv_addr}:{dest_port}, '
#             f'конечный компьютер отверг запрос на подключение.')
#         sys.exit(1)
    

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
    
    # Сообщаем о запуске
    print('Запуск клиентского модуля.')

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = client_args_parser()

    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке то запросим его
    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)
    print("///CLN_main_1", client_name)
    
    # Записываем логи
    CLIENT_LOGGER.info(
        f"Запущен клиент с парамертами: адрес сервера: {server_address} ,"
        f" порт: {server_port}, имя пользователя: {client_name}")

    # Создаём объект базы данных
    database = ClientDatabase(client_name)
    print("///CLN_main_2", database)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        client = Client(server_port, server_address, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    client.setDaemon(True)
    client.start()
    print("///CLN_main_3", client)
    status = f"Client Working. Server address: {server_address}. Server port: {server_port}"

    # Создаём GUI
    main_window = ClientMainWindow(database, client, status)
    main_window.make_connection(client)
    main_window.setWindowTitle(f'Чат Программа Auuu - [{client_name}]')
    client_app.exec_()
    print("///CLN_main_4", main_window)

    # Раз графическая оболочка закрылась, закрываем транспорт
    client.transport_shutdown()
    client.join()


if __name__ == '__main__':
    main()

