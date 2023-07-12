import os
import sys
import json
import time
import threading
import argparse
import socket
import hashlib
import hmac
import binascii
from dotenv import load_dotenv
from datetime import datetime
from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject
import logging

project_directory = os.getcwd()
sys.path.append(project_directory)
# print("///CLN_000",project_directory)
import log.client_log_config
from log.decor_log import log
from common.utils import ClientVerifier
from common.errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from client.ui_start_dialog import UserNameDialog
from client.client_database import ClientDatabase
from client.client_main_window import ClientMainWindow




CLIENT_LOGGER = logging.getLogger('client')
socket_lock = threading.Lock()


class Client(threading.Thread, QObject):
    '''
    Класс реализующий транспортную подсистему клиентского
    модуля. Отвечает за взаимодействие с сервером.
    '''
    # Сигналы новое сообщение и потеря соединения
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, client_name, passwd, keys):
        # Вызываем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        # Класс База данных - работа с базой
        self.database = database
        # Имя пользователя
        self.username = client_name
        # Пароль
        self.password = passwd
        # Набор ключей для шифрования
        self.keys = keys
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
            CLIENT_LOGGER.error(
                'Timeout соединения при обновлении списков пользователей.')
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
            CLIENT_LOGGER.critical(
                'Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        CLIENT_LOGGER.debug(
            'Установлено соединение с сервером, запускаем авторизацию')

        # Запускаем процедуру авторизации
        # Получаем хэш пароля
        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        CLIENT_LOGGER.debug(f'Passwd hash ready: {passwd_hash_string}')

        # Получаем публичный ключ и декодируем его из байтов
        pubkey = self.keys.publickey().export_key().decode('ascii')

        # Авторизируемся на сервере
        with socket_lock:
            presense = {
                os.getenv('ACTION'): os.getenv('PRESENCE'),
                os.getenv('TIME'): time.time(),
                os.getenv('USER'): {
                    os.getenv('ACCOUNT_NAME'): self.username,
                    os.getenv('PUBLIC_KEY'): pubkey
                }
            }
            CLIENT_LOGGER.debug(f"Presense message = {presense}")
            # Отправляем серверу приветственное сообщение.
            try:
                self.send_message(self.s, presense)
                ans = self.get_message(self.s)
                CLIENT_LOGGER.debug(f'Server response = {ans}.')
                # Если сервер вернул ошибку, бросаем исключение.
                if os.getenv('RESPONSE') in ans:
                    if ans[os.getenv('RESPONSE')] == 400:
                        raise ServerError(ans[os.getenv('ERROR')])
                    elif ans[os.getenv('RESPONSE')] == 511:
                        # Если всё нормально, то продолжаем процедуру
                        # авторизации.
                        ans_data = ans[os.getenv('DATA')]
                        hash = hmac.new(passwd_hash_string,
                                        ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = {
                            os.getenv('RESPONSE'): 511,
                            os.getenv('DATA'): None
                        }
                        my_ans[os.getenv('DATA')] = binascii.b2a_base64(
                            digest).decode('ascii')
                        self.send_message(self.s, my_ans)
                        self.process_server_ans(self.get_message(self.s))
            except (OSError, json.JSONDecodeError) as err:
                CLIENT_LOGGER.debug(f'Connection error.', exc_info=err)
                raise ServerError('Сбой соединения в процессе авторизации.')

    @log
    def send_message(self, open_socket, message):
        '''
        Функция отправки словарей через сокет.
        Кодирует словарь в формат JSON и отправляет через сокет.
        :param open_socket: сокет для передачи
        :param message: словарь для передачи
        :return: ничего не возвращает
        '''
        js_message = json.dumps(message)
        print("///CLN__SM_1", "[message:]", message,
              "\n[js_message:]", js_message, "\n")
        encoded_message = js_message.encode(os.getenv('ENCODING'))
        open_socket.send(encoded_message)
        print("///CLN__SM_2", "[message:]", message,
              "\n[encoded_message:]", encoded_message,
              "\n[open_socket:]", open_socket, "\n")

    @log
    def get_message(self, client):
        """
        Функция приёма сообщений от удалённых компьютеров.
        Принимает сообщения JSON, декодирует полученное сообщение
        и проверяет что получен словарь.
        :param client: сокет для передачи данных.
        :return: словарь - сообщение.
        """
        encoded_response = client.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
        # print("CLN__GM_1", encoded_response, "||||")
        json_response = encoded_response.decode(os.getenv('ENCODING'))
        response_dict = json.loads(json_response)
        if isinstance(response_dict, dict):
            # print("CLN__GM_2", response_dict, "||||")
            return response_dict
        else:
            raise TypeError

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
        CLIENT_LOGGER.debug(
            f"Сформировано {os.getenv('PRESENCE')} сообщение для пользователя {self.username}")
        return message

    def process_server_ans(self, message):
        '''Метод обработчик поступающих сообщений с сервера.'''
        CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')
        print("/\/CLN_psa_1", "message:", message)

        # Если это подтверждение чего-либо
        if os.getenv('RESPONSE') in message:
            if message[os.getenv('RESPONSE')] == 200:
                return
            elif message[os.getenv('RESPONSE')] == 400:
                raise ServerError(f"{message[os.getenv('ERROR')]}")
            elif message[os.getenv('RESPONSE')] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                CLIENT_LOGGER.debug(
                    f"Принят неизвестный код подтверждения {message[os.getenv('RESPONSE')]}")

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о
        # новом сообщении
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
                and os.getenv('SENDER') in message \
                and os.getenv('DESTINATION') in message \
                and os.getenv('MESSAGE_TEXT') in message \
                and message[os.getenv('DESTINATION')] == self.username:
            print("/\/CLN_psa_2", "message:",
                  message[os.getenv('MESSAGE_TEXT')])
            CLIENT_LOGGER.debug(
                f"Получено сообщение от пользователя {message[os.getenv('SENDER')]}:{message[os.getenv('MESSAGE_TEXT')]}")
            self.new_message.emit(message)
            print("/\/CLN_psa_3", "message:",
                  message[os.getenv('MESSAGE_TEXT')])

    def contacts_list_update(self):
        '''Метод обновляющий с сервера список контактов.'''
        self.database.contacts_clear()
        CLIENT_LOGGER.debug(
            f'Запрос контакт листа для пользователся {self.username}')
        req = {
            os.getenv('ACTION'): os.getenv('GET_CONTACTS'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): self.username
        }
        CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
        with socket_lock:
            self.send_message(self.s, req)
            ans = self.get_message(self.s)
        CLIENT_LOGGER.debug(f'Получен ответ {ans}')
        if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 202:
            for contact in ans[os.getenv('LIST_INFO')]:
                self.database.add_contact(contact)
        else:
            CLIENT_LOGGER.error('Не удалось обновить список контактов.')

    def user_list_update(self):
        '''Метод обновляющий с сервера список пользователей.'''
        print("///CLN_ulu_1", self.username)
        CLIENT_LOGGER.debug(
            f'Запрос списка известных пользователей {self.username}')
        req = {
            os.getenv('ACTION'): os.getenv('USERS_REQUEST'),
            os.getenv('TIME'): time.time(),
            os.getenv('ACCOUNT_NAME'): self.username
        }
        with socket_lock:
            self.send_message(self.s, req)
            ans = self.get_message(self.s)
        if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 202:
            self.database.add_users(ans[os.getenv('LIST_INFO')])
        else:
            CLIENT_LOGGER.error(
                'Не удалось обновить список известных пользователей.')

    def key_request(self, user):
        '''Метод запрашивающий с сервера публичный ключ пользователя.'''
        CLIENT_LOGGER.debug(f'Запрос публичного ключа для {user}')
        req = {
            os.getenv('ACTION'): os.getenv('PUBLIC_KEY_REQUEST'),
            os.getenv('TIME'): time.time(),
            os.getenv('ACCOUNT_NAME'): user
        }
        with socket_lock:
            self.send_message(self.s, req)
            ans = self.get_message(self.s)
        if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 511:
            return ans[os.getenv('DATA')]
        else:
            CLIENT_LOGGER.error(f'Не удалось получить ключ собеседника{user}.')

    def add_contact(self, contact):
        '''Метод отправляющий на сервер сведения о добавлении контакта.'''
        CLIENT_LOGGER.debug(f'Создание контакта {contact}')
        req = {
            os.getenv('ACTION'): os.getenv('ADD_CONTACT'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): self.username,
            os.getenv('ACCOUNT_NAME'): contact
        }
        with socket_lock:
            self.send_message(self.s, req)
            self.process_server_ans(self.get_message(self.s))

    def remove_contact(self, contact):
        '''Метод отправляющий на сервер сведения о удалении контакта.'''
        CLIENT_LOGGER.debug(f'Удаление контакта {contact}')
        req = {
            os.getenv('ACTION'): os.getenv('REMOVE_CONTACT'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): self.username,
            os.getenv('ACCOUNT_NAME'): contact
        }
        with socket_lock:
            self.send_message(self.s, req)
            self.process_server_ans(self.get_message(self.s))

    def transport_shutdown(self):
        '''Метод уведомляющий сервер о завершении работы клиента.'''
        self.running = False
        message = {
            os.getenv('ACTION'): os.getenv('EXIT'),
            os.getenv('TIME'): time.time(),
            os.getenv('ACCOUNT_NAME'): self.username
        }
        with socket_lock:
            try:
                self.send_message(self.s, message)
            except OSError:
                pass
        CLIENT_LOGGER.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    def send_data(self, to, message):
        '''Метод отправки сообщения пользователю на сервер.'''
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
            self.send_message(self.s, message_dict)
            self.process_server_ans(self.get_message(self.s))
            CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        '''Основной цикл работы транспортного потока.'''
        print("/\/CLN_run_1", "message:")
        CLIENT_LOGGER.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то отправка может достаточно долго
            # ждать освобождения сокета.
            time.sleep(1)
            message = None
            with socket_lock:
                try:
                    # print("/\/CLN_run_2", "message:", message)
                    self.s.settimeout(0.5)
                    message = self.get_message(self.s)
                except OSError as err:
                    if err.errno:
                        CLIENT_LOGGER.critical(
                            f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    CLIENT_LOGGER.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    self.s.settimeout(5)

            # Если сообщение получено, то вызываем функцию обработчик:
            if message:
                CLIENT_LOGGER.debug(f'Принято сообщение с сервера: {message}')
                print("/\/CLN_run_3", "message:", message)
                self.process_server_ans(message)


@log
def client_args_parser():
    """     
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов
    адрес сервера, порт, имя пользователя, пароль.
    Выполняет проверку на корректность номера порта. 
    """
    parser = argparse.ArgumentParser(description='Client script')
    parser.add_argument('addr', default=os.getenv('DEFAULT_IP_ADDRESS'), type=str, nargs='?',
                        help="Параметр 'addr' позволяет указать IP-адрес, с которого будут приниматься соединения. (по умолчанию адрес не указан, ")
    parser.add_argument('port', default=os.getenv('DEFAULT_PORT'), type=int, nargs='?',
                        help="Параметр 'port' позволяет указать порт сервера (по умолчанию 7777)")
    parser.add_argument('-n', '--name', default=None, nargs='?',
                        help="Параметр '-n' позволяет указать имя пользователя при запуске")
    parser.add_argument('-p', '--password', default='', nargs='?',
                        help="Параметр '-p' позволяет указать пароль пользователя при запуске")

    args = parser.parse_args(sys.argv[1:])
    serv_addr = args.addr
    serv_port = args.port
    client_name = args.name
    client_passwd = args.password

    # проверим подходящий номер порта
    if not 1023 < serv_port < 65536:
        CLIENT_LOGGER.critical(f"Попытка запуска клиента с неподходящим номером порта удалённого сервера: {serv_port}. "
                               f"Допустимы адреса с 1024 до 65535. Клиенту будет принудительно установлен порт подключения к удалённому серверу по умолчанию : {os.getenv('DEFAULT_PORT')}")
        serv_port = os.getenv('DEFAULT_PORT')

    return serv_addr, serv_port, client_name, client_passwd


def main():
    load_dotenv()

    # Сообщаем о запуске
    print('Запуск клиентского модуля.')

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name, client_passwd = client_args_parser()

    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке то запросим его

    if not client_name or not client_passwd:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и
        # удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            CLIENT_LOGGER.debug(
                f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
            del start_dialog
        else:
            sys.exit(0)
    print("///CLN_main_1", client_name)

    # Записываем логи
    CLIENT_LOGGER.info(
        f"Запущен клиент с параметрами: адрес сервера: {server_address} ,"
        f" порт: {server_port}, имя пользователя: {client_name}")

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    key_file = os.path.join(
        f'{project_directory}/client', f'priv_{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    # Создаём объект базы данных
    database = ClientDatabase(client_name)
    print("///CLN_main_2", database)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        client = Client(server_port, server_address, database,
                        client_name, client_passwd, keys)
    except ServerError as error:
        message = QMessageBox()
        message.critical('Ошибка сервера', error.text)
        sys.exit(1)

    client.setDaemon(True)
    client.start()
    print("///CLN_main_3", client)

    status = f"Client Working. Server address: {server_address}. Server port: {server_port}"

    # Создаём GUI
    main_window = ClientMainWindow(database, client, keys, status)
    print("///CLN_main_4", main_window)
    main_window.make_connection(client)
    print("///CLN_main_5", main_window)
    main_window.setWindowTitle(f'Чат Программа Auuu - [{client_name}]')
    client_app.exec_()
    print("///CLN_main_6", main_window)

    # Раз графическая оболочка закрылась, закрываем транспорт
    client.transport_shutdown()
    client.join()


if __name__ == '__main__':
    main()
