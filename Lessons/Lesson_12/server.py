import os, sys, json, select, time, argparse, socket, threading, configparser
from dotenv import load_dotenv
import logging
import log.server_log_config
from log.decor_log import log
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from server_database import ServerStorage
from utils import DescriptorAddress, DescriptorPort, ServerVerifier

# Флаг что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()


class Server(threading.Thread, metaclass=ServerVerifier):

    serv_addr = DescriptorAddress()
    listen_port = DescriptorPort()

    def __init__(self, db):
        
        # Конструктор предка
        super().__init__()
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SERVER_LOGGER = logging.getLogger('server')
        # Очередь ожидающих клиентов
        self.clients = []
        # Очередь сообщений
        self.messages = []
        # Словарь, содержащий имена пользователей и соответствующие им сокеты
        self.names = {}
        # База данных
        self.database = db

        # self.run()


    @log
    def send_message(self, open_socket, message):
        json_message = json.dumps(message)
        response = json_message.encode(os.getenv('ENCODING'))
        open_socket.send(response)
        print("///SERV_SM_1", "[message:]", message, "\n[response:]", response, "\n[open_socket:]", open_socket, "\n")

    @log
    def get_message(self, client):
        """
        Утилита приёма и декодирования сообщения принимает байты выдаёт словарь,
        если приняточто-то другое отдаёт ошибку значения
        :param client:
        :return:
        """
        response = client.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
        # print("SERV_GM_1", response, "||||")
        if isinstance(response, bytes):
            json_response = response.decode(os.getenv('ENCODING'))
            response_dict = json.loads(json_response)
            if isinstance(response_dict, dict):
                # print("SERV_GM_2", response_dict, "||||")
                return response_dict
            raise ValueError
        raise ValueError


    @log
    def process_client_message(self, message,  client):
        """
        Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости.
        """
        
        global new_connection
        self.SERVER_LOGGER.debug(f"Разбор сообщения от клиента : {message}")
        print("///SERV_PCM1 [names:]", self.names, "\n[message:]", message, "\n[client:]", client)
        # Если это сообщение о присутствии, принимаем и отвечаем
        if os.getenv('ACTION') in message \
                    and message[os.getenv('ACTION')] == os.getenv('PRESENCE') \
                    and os.getenv('TIME') in message \
                    and os.getenv('USER') in message:
            # Если такой пользователь ещё не зарегистрирован,
            # регистрируем, иначе отправляем ответ и завершаем соединение.
            print("///SERV_PCM2 [names:]", self.names, "\n[message:]", message)
            if message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')] not in self.names.keys():
                self.names[message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')]] = client
                # print("SERV_PCM3", "[names:]", self.names, "\n[message:]", message)
                client_ip, client_port = client.getpeername()
                print("///SERV_PCM4", message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')],  client_ip,  client_port)
                self.database.user_login(message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')], client_ip, client_port)
                self.send_message(client, {os.getenv('RESPONSE'): 200})
                with conflag_lock:
                    new_connection = True
            else:
                self.send_message(client, {
                    os.getenv('RESPONSE'): 409,
                    os.getenv('ERROR'): 'Username already in use.'
                })
                self.clients.remove(client)
                client.close()       
            return
        # Если это сообщение, то добавляем его в очередь сообщений.
        # Ответ не требуется.
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
                and os.getenv('DESTINATION') in message \
                and os.getenv('TIME') in message \
                and os.getenv('SENDER') in message \
                and os.getenv('MESSAGE_TEXT') in message:
            self.messages.append(message)
            return

        # Отправляем по запросу список пользователей подключённых к серверу
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('GETULIST') \
                and os.getenv('TIME') in message \
                and os.getenv('USER') in message:
            # print("SERV_GUL1 [names:]", self.names)
            # print(list(self.names.keys()))
            # print(' '.join(list(names.keys())))
            users = ' '.join(list(self.names.keys()))
            self.send_message(client, {
                os.getenv('ACTION'): os.getenv('GETULIST'),
                os.getenv('USERS_LIST'): users
            })
            return

        # Если клиент выходит
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('EXIT') \
                and os.getenv('ACCOUNT_NAME') in message:
            self.database.user_logout(message[os.getenv('ACCOUNT_NAME')])
            self.SERVER_LOGGER.debug(
                f"Клиент {message[os.getenv('ACCOUNT_NAME')]} корректно отключился от сервера.")
            self.clients.remove(self.names[message[os.getenv('ACCOUNT_NAME')]])
            self.names[message[os.getenv('ACCOUNT_NAME')]].close()
            del self.names[message[os.getenv('ACCOUNT_NAME')]]
            with conflag_lock:
                new_connection = True
            return

                # Если это запрос контакт-листа
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('GET_CONTACTS') \
                and os.getenv('USER') in message \
                and self.names[message[os.getenv('USER')]] == client:
            response = {os.getenv('RESPONSE'): 202, os.getenv('LIST_INFO'): None}
            response[os.getenv('LIST_INFO')] = self.database.get_contacts(message[os.getenv('USER')])
            self.send_message(client, response)

        # Если это добавление контакта
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('ADD_CONTACT') \
                and os.getenv('ACCOUNT_NAME') in message and os.getenv('USER') in message \
                and self.names[message[os.getenv('USER')]] == client:
            self.database.add_contact(message[os.getenv('USER')], message[os.getenv('ACCOUNT_NAME')])
            self.send_message(client, {os.getenv('RESPONSE'): 200})

        # Если это удаление контакта
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('REMOVE_CONTACT') \
                and os.getenv('ACCOUNT_NAME') in message \
                and os.getenv('USER') in message \
                and self.names[message[os.getenv('USER')]] == client:
            self.database.remove_contact(message[os.getenv('USER')], message[os.getenv('ACCOUNT_NAME')])
            self.send_message(client, {os.getenv('RESPONSE'): 200})

        # Если это запрос известных пользователей
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('USERS_REQUEST') \
                and os.getenv('ACCOUNT_NAME') in message \
                and self.names[message[os.getenv('ACCOUNT_NAME')]] == client:
            print("/\/SERV_PCM6 [names:]", self.names, "\n[message:]", message)
            response = {os.getenv('RESPONSE'): 202, os.getenv('LIST_INFO'): None}
            print("/\/SERV_PCM7 [response:]", response, "\n[users_list:]", self.database.users_list() )
            response[os.getenv('LIST_INFO')] = [user[0]
                                   for user in self.database.users_list()]
            print("/\/SERV_PCM8 [response:]", response)
            self.send_message(client, response)
            print("/\/SERV_PCM9 [response:]", response)

        # Иначе отдаём Bad request
        else:
            response = {os.getenv('RESPONSE'): 400, os.getenv('ERROR'): None}
            response[os.getenv('ERROR')] = 'Bad request.'
            self.send_message(client, response)
            return

    @log
    def process_message(self, message, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь-сообщение,
        список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
        :param os.getenv('MESSAGE'):
        :param names:
        :param listen_socks:
        :return:
        """
        if message[os.getenv('DESTINATION')] in self.names \
                and self.names[message[os.getenv('DESTINATION')]] in listen_socks:
            self.send_message(self.names[message[os.getenv('DESTINATION')]], message)
            self.SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[os.getenv("DESTINATION")]} '
                        f'от пользователя {message[os.getenv("SENDER")]}.')
        elif message[os.getenv('DESTINATION')] in self.names\
                and self.names[message[os.getenv('DESTINATION')]] not in listen_socks:
            raise ConnectionError
        else:
            self.SERVER_LOGGER.os.getenv('ERROR')(
                f'Пользователь {message[os.getenv("DESTINATION")]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')  


    @log
    def srv_args_parser(self):
        """ Парсер аргументов коммандной строки """
        # print("///SERV_gap_1: ",os.getenv('DEFAULT_IP_ADDRESS'),  os.getenv('DEFAULT_PORT'))
        parser = argparse.ArgumentParser(description='Server script')
        parser.add_argument('-a', default=os.getenv('DEFAULT_IP_ADDRESS'), type=str, nargs='?', \
            help='Параметр -a позволяет указать IP-адрес, с которого будут приниматься соединения. (по умолчанию адрес не указан, ')
        parser.add_argument('-p', default=os.getenv('DEFAULT_PORT'), type=int, nargs='?', \
            help='Параметр -p позволяет указать порт сервера (по умолчанию 7777)')
        
        args = parser.parse_args(sys.argv[1:])
        self.serv_addr = args.a
        self.listen_port = args.p
    
    
    def run(self):
        """
        Запуск сервера
        """
        load_dotenv()

        self.srv_args_parser()

        self.SERVER_LOGGER.info(
            f'Серверный модуль запущен. '
            f'Адрес: {self.serv_addr} Порт: {self.listen_port}\n')
        # print( f'Консольный месседжер. Серверный модуль запущен.\n'
        #     f'Адрес: {self.serv_addr} Порт: {self.listen_port}\n')
        
        # print("///SERV_run_1: ",self.serv_addr,  self.listen_port)
        self.s.bind((self.serv_addr, int(self.listen_port)))
        self.s.settimeout(0.5) # Таймаут для операций с сокетом
        self.s.listen(int(os.getenv('MAX_CONNECTIONS')))

        # Основной цикл программы сервера
        while True:
            try:
                client_sock, client_address = self.s.accept()
            except OSError:
                pass # timeout вышел
            else:
                self.SERVER_LOGGER.info(f'Получен запрос на соединение от {client_address}')
                self.clients.append(client_sock)
            
            rlist = [] #список объектов, по готовности из которых нужно что-то прочитать
            wlist = [] #список объектов, по готовности в которые нужно что-то записать
            err_lst = [] #список объектов, в которых возможно будут ошибки
            
            # print("///SERV_0 ", "[clients: ]", self.clients, "\n")
            # Проверка на наличие ждущих клиентов
            try:
                if self.clients:
                    rlist, wlist, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                self.SERVER_LOGGER.error(f'Ошибка работы с сокетами: {err}')
            
            # print("///SERV_1 ", "[rlist:]", rlist, "\n[wlist:]", wlist, "\n[names:]", self.names, "\n[messages:]", self.messages, "\n")
            # принимаем сообщения и если там есть сообщения,
            # кладём в словарь, если ошибка, исключаем клиента.
            if rlist:
                for client_with_message in rlist:
                    try:
                        # print("///SERV_11 ", "[client_with_message: ]", client_with_message, "\n")
                        self.process_client_message(self.get_message(client_with_message),
                                    client_with_message)
                    except Exception:
                        self.SERVER_LOGGER.info(f'Отправляющий клиент '
                            f'{client_with_message.getpeername()} отключился от сервера.')
                        print(f'Отправляющий клиент '
                            f'{client_with_message.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
            
            # print("///SERV_2 ", "[rlist:]", rlist, "\n[wlist:]", wlist, "\n[names:]", self.names, "\n[messages:]", self.messages, "\n")
            # Если есть сообщения, обрабатываем каждое.
            for message in self.messages:
                try:
                    # print("///SERV_3 ","[names:]", self.names, "\n[i:]", i)
                    self.process_message(message, wlist)
                except Exception:
                    self.SERVER_LOGGER.info(f'Связь с клиентом с именем '
                        f'{message[os.getenv("DESTINATION")]} была потеряна при отправке сообщения')
                    print(f'Связь с клиентом с именем '
                        f'{message[os.getenv("DESTINATION")]} была потеряна при отправке сообщения')
                    self.clients.remove(self.names[message[os.getenv('DESTINATION')]])
                    self.database.user_logout(message[os.getenv('DESTINATION')])
                    del self.names[i[os.getenv('DESTINATION')]]
            self.messages.clear()    
        

def main():
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

     
    # Инициализация базы данных
    path_to_db = os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file'])
    print("///SERV_main_0: ",type("///SERV_main_1: "), ',',  path_to_db)
    database = ServerStorage(path_to_db)
    print("///SERV_main_1: ", database)
    
    # Создание экземпляра класса - сервера и его запуск:
    server = Server(database)
    server.daemon = True
    server.start()
    print("///SERV_main_2")

    # Создаём графическое окуружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()
    

    # Функция обновляющяя список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def list_update():
        global new_connection
        # print("///SERV_main_3", new_connection)
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    # timer.timeout.connect(database.active_users_list)
    timer.start(1000)



    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)
    print("///SERV_main_4")

    # Запускаем GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
