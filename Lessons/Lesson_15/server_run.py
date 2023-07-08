import os, sys, json, select, time, argparse, socket, threading, configparser, hmac, binascii
from dotenv import load_dotenv
import logging
import log.server_log_config
from log.decor_log import log, login_required
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from server.ui_server_main_window import MainWindow
from server.server_database import ServerStorage
from common.utils import DescriptorAddress, DescriptorPort, ServerVerifier



class Server(threading.Thread, metaclass=ServerVerifier):

    serv_addr = DescriptorAddress()
    listen_port = DescriptorPort()

    def __init__(self, serv_addr, listen_port, db):
        
        # Конструктор предка
        super().__init__()

        # Параментры подключения
        self.serv_addr = serv_addr
        self.listen_port = listen_port
                
        self.SERVER_LOGGER = logging.getLogger('server')
        # Очередь ожидающих клиентов
        self.clients = []
        # Очередь сообщений
        self.messages = []
        # Словарь, содержащий имена пользователей и соответствующие им сокеты
        self.names = {}
        # База данных
        self.database = db
        # Флаг продолжения работы
        self.running = True
        # Сокеты
        self.wlist = None

        # self.run()


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
        encoded_message = js_message.encode(os.getenv('ENCODING'))
        open_socket.send(encoded_message)
        print("///SERV_SM_1", "[message:]", message, \
            "\n[encoded_message:]", encoded_message, \
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
        print("SERV_GM_1", encoded_response, "||||")
        json_response = encoded_response.decode(os.getenv('ENCODING'))
        response_dict = json.loads(json_response)
        if isinstance(response_dict, dict):
            print("SERV_GM_2", response_dict, "||||")
            return response_dict
        else:
            raise TypeError


    @login_required
    def process_client_message(self, message,  client):
        """
        Метод обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости.
        """      
        self.SERVER_LOGGER.debug(f"Разбор сообщения от клиента : {message}")
        print("///SERV_PCM1 [names:]", self.names, "\n[message:]", message, "\n[client:]", client)
        # Если это сообщение о присутствии, принимаем и отвечаем
        if os.getenv('ACTION') in message \
                    and message[os.getenv('ACTION')] == os.getenv('PRESENCE') \
                    and os.getenv('TIME') in message \
                    and os.getenv('USER') in message:
            # Если сообщение о присутствии то вызываем функцию авторизации.
            self.autorize_user(message, client)


        # Если это сообщение, то отправляем его получателю.
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
                and os.getenv('DESTINATION') in message \
                and os.getenv('TIME') in message \
                and os.getenv('SENDER') in message \
                and os.getenv('MESSAGE_TEXT') in message \
                and self.names[message[os.getenv('SENDER')]] == client:
            if message[os.getenv('DESTINATION')] in self.names:
                self.database.process_message(message[os.getenv('SENDER')], message[os.getenv('DESTINATION')])
                self.send_data(message)
                try:
                    self.send_message(client, {os.getenv('RESPONSE'): 200})
                except OSError:
                    self.remove_client(client)
            else:
                response = {
                    os.getenv('RESPONSE'): 400, 
                    os.getenv('ERROR'): 'User not registered on the server.'
                    }
                self.send_message(client, response)
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
                and os.getenv('ACCOUNT_NAME') in message \
                and self.names[message[os.getenv('ACCOUNT_NAME')]] == client:
            self.remove_client(client)
            self.SERVER_LOGGER.debug(
                f"Клиент {message[os.getenv('ACCOUNT_NAME')]} корректно отключился от сервера.")

        # Если это запрос контакт-листа
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('GET_CONTACTS') \
                and os.getenv('USER') in message \
                and self.names[message[os.getenv('USER')]] == client:
            response = {os.getenv('RESPONSE'): 202, os.getenv('LIST_INFO'): None}
            print("/\/SERV_PCMGC_1 [response:]", response)
            response[os.getenv('LIST_INFO')] = self.database.get_contacts(message[os.getenv('USER')])  
            print("/\/SERV_PCMGC_2 [response:]", response)          
            try:
                self.send_message(client, response)
                print("/\/SERV_PCMGC_3 [response:]", response, "\n[client:]", client) 
            except OSError:
                self.remove_client(client)

        # Если это добавление контакта
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('ADD_CONTACT') \
                and os.getenv('ACCOUNT_NAME') in message \
                and os.getenv('USER') in message \
                and self.names[message[os.getenv('USER')]] == client:
            self.database.add_contact(message[os.getenv('USER')], message[os.getenv('ACCOUNT_NAME')]) 
            try:
                self.send_message(client, {os.getenv('RESPONSE'): 200})
            except OSError:
                self.remove_client(client)

        # Если это удаление контакта
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('REMOVE_CONTACT') \
                and os.getenv('ACCOUNT_NAME') in message \
                and os.getenv('USER') in message \
                and self.names[message[os.getenv('USER')]] == client:
            self.database.remove_contact(message[os.getenv('USER')], message[os.getenv('ACCOUNT_NAME')])
            try:
                self.send_message(client, {os.getenv('RESPONSE'): 200})
            except OSError:
                self.remove_client(client)

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
            try:
                self.send_message(client, response)
            except OSError:
                self.remove_client(client)
        
        # Если это запрос публичного ключа пользователя
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('PUBLIC_KEY_REQUEST') \
                and os.getenv('ACCOUNT_NAME') in message:
            response = {
                    os.getenv('RESPONSE'): 511, 
                    os.getenv('DATA'): None
                }
            response[os.getenv('DATA')] = self.database.get_pubkey(message[os.getenv('ACCOUNT_NAME')])
            # может быть, что ключа ещё нет (пользователь никогда не логинился,
            # тогда шлём 400)
            if response[os.getenv('DATA')]:
                try:
                    self.send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = {
                    os.getenv('RESPONSE'): 400, 
                    os.getenv('ERROR'): None
                }
                response[os.getenv('ERROR')] = 'No public key for this user'
                try:
                    self.send_message(client, response)
                except OSError:
                    self.remove_client(client)

        # Иначе отдаём Bad request
        else:
            response = {
                os.getenv('RESPONSE'): 400, 
                os.getenv('ERROR'): 'Bad request.'
                }
            try:
                self.send_message(client, response)
            except OSError:
                self.remove_client(client)
   

    def autorize_user(self, message, sock):
        '''Метод реализующий авторизцию пользователей.'''
        # Если имя пользователя уже занято то возвращаем 400
        self.SERVER_LOGGER.debug(f"Start auth process for {message[os.getenv('USER')]}")
        if message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')] in self.names.keys():
            response = {
                    os.getenv('RESPONSE'): 400, 
                    os.getenv('ERROR'): None
                }
            response[os.getenv('ERROR')] = 'Username already taken.'
            try:
                self.SERVER_LOGGER.debug(f'Username busy, sending {response}')
                self.send_message(sock, response)
            except OSError:
                self.SERVER_LOGGER.debug('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()
        # Проверяем что пользователь зарегистрирован на сервере.
        elif not self.database.check_user(message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')]):
            response = {
                    os.getenv('RESPONSE'): 400, 
                    os.getenv('ERROR'): None
                }
            response[os.getenv('ERROR')] = 'User not registered.'
            try:
                self.SERVER_LOGGER.debug(f'Unknown username, sending {response}')
                self.send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            self.SERVER_LOGGER.debug('Correct username, starting passwd check.')
            # Иначе отвечаем 511 и проводим процедуру авторизации
            # Словарь - заготовка
            message_auth = {
                    os.getenv('RESPONSE'): 511, 
                    os.getenv('DATA'): None
                }
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            message_auth[os.getenv('DATA')] = random_str.decode('ascii')
            # Создаём хэш пароля и связки с рандомной строкой, сохраняем
            # серверную версию ключа
            hash = hmac.new(self.database.get_hash(message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')]), random_str, 'MD5')
            digest = hash.digest()
            self.SERVER_LOGGER.debug(f'Auth message = {message_auth}')
            try:
                # Обмен с клиентом
                self.send_message(sock, message_auth)
                ans = self.get_message(sock)
            except OSError as err:
                self.SERVER_LOGGER.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[os.getenv('DATA')])
            # Если ответ клиента корректный, то сохраняем его в список
            # пользователей.
            if os.getenv('RESPONSE') in ans and ans[os.getenv('RESPONSE')] == 511 and hmac.compare_digest(
                    digest, client_digest):
                self.names[message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    self.send_message(sock, {os.getenv('RESPONSE'): 200})
                except OSError:
                    self.remove_client(message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')])
                # добавляем пользователя в список активных и если у него изменился открытый ключ
                # сохраняем новый
                self.database.user_login(
                    message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')],
                    client_ip,
                    client_port,
                    message[os.getenv('USER')][os.getenv('PUBLIC_KEY')])
            else:
                response = {
                    os.getenv('RESPONSE'): 400, 
                    os.getenv('ERROR'): None
                }
                response[os.getenv('ERROR')] = 'Incorrect password.'
                try:
                    self.send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()


    def service_update_lists(self):
        '''Метод реализующий отправки сервисного сообщения 205 клиентам.'''
        for client in self.names:
            try:
                self.send_message(self.names[client], {os.getenv('RESPONSE'): 205})
            except OSError:
                self.remove_client(self.names[client])


    def send_data(self, message):
        '''
        Метод отправки сообщения клиенту.
        '''
        print("/\/SERV_SD_1 [message:]", message)
        if message[os.getenv('DESTINATION')] in self.names \
                and self.names[message[os.getenv('DESTINATION')]
        ] in self.wlist:
            print("/\/SERV_SD_2 [message:]", message)
            try:
                self.send_message(self.names[message[os.getenv('DESTINATION')]], message)
                self.SERVER_LOGGER.info(f'Пользователь {message[os.getenv("SENDER")]}  '
                f'отправил сообщение пользователю {message[os.getenv("DESTINATION")]}: {message[os.getenv("MESSAGE_TEXT")]}.')
            except OSError:
                self.remove_client(message[os.getenv('DESTINATION')])
        
        elif message[os.getenv('DESTINATION')] in self.names \
                and self.names[message[os.getenv('DESTINATION')]] not in self.wlist:
            print("/\/SERV_SD_3 [message:]", message)
            self.SERVER_LOGGER.error(
                f"Связь с клиентом {message[os.getenv('DESTINATION')]} была потеряна. Соединение закрыто, доставка невозможна.")
            self.remove_client(self.names[message[os.getenv('DESTINATION')]])
        
        else:
            self.SERVER_LOGGER.error(
                f"Пользователь {message[os.getenv('DESTINATION')]} не зарегистрирован на сервере, отправка сообщения невозможна.")

   
    def remove_client(self, client):
        '''
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        '''
        self.SERVER_LOGGER.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()
  
    
    def run(self):
        """
        Запуск сервера
        """
        # load_dotenv()

        self.SERVER_LOGGER.info(
            f'Серверный модуль запущен. '
            f'Адрес: {self.serv_addr} Порт: {self.listen_port}\n')
        print(
            f'Серверный модуль запущен. '
            f'Адрес: {self.serv_addr} Порт: {self.listen_port}\n')
 
        
        # print("///SERV_run_1: ",str(self.serv_addr), type(self.serv_addr), self.listen_port, type(self.listen_port))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.serv_addr, int(self.listen_port)))
        s.settimeout(0.5) # Таймаут для операций с сокетом
        s.listen(int(os.getenv('MAX_CONNECTIONS')))

        # Основной цикл программы сервера
        while True:
            try:
                client_sock, client_address = s.accept()
            except OSError:
                pass # timeout вышел
            else:
                self.SERVER_LOGGER.info(f'Получен запрос на соединение от {client_address}')
                self.clients.append(client_sock)
            
            rlist = [] #список объектов, по готовности из которых нужно что-то прочитать
            self.wlist = [] #список объектов, по готовности в которые нужно что-то записать
            err_lst = [] #список объектов, в которых возможно будут ошибки
            
            # print("///SERV_0 ", "[clients: ]", self.clients, "\n")
            # Проверка на наличие ждущих клиентов
            try:
                if self.clients:
                    rlist, self.wlist, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                self.SERVER_LOGGER.error(f'Ошибка работы с сокетами: {err}')
            
            # print("///SERV_1 ", "[rlist:]", rlist, "\n[wlist:]", self.wlist, "\n[names:]", self.names, "\n[messages:]", self.messages, "\n")
            # принимаем сообщения и если там есть сообщения,
            # кладём в словарь, если ошибка, исключаем клиента.
            if rlist:
                for client_with_message in rlist:
                    try:
                        # print("///SERV_11 ", "[client_with_message: ]", client_with_message, "\n")
                        self.process_client_message(self.get_message(client_with_message),
                                    client_with_message)
                    except (OSError):
                        self.SERVER_LOGGER.info(f'Отправляющий клиент '
                            f'{client_with_message.getpeername()} отключился от сервера.')
                        print(f'Отправляющий клиент '
                            f'{client_with_message.getpeername()} отключился от сервера.')
                        self.remove_client(client_with_message)


"""
###############################################################################
"""

def srv_args_parser(default_address, default_port):
    """ Парсер аргументов коммандной строки """
    # print("///SERV_gap_1: ",os.getenv('DEFAULT_IP_ADDRESS'),  os.getenv('DEFAULT_PORT'))
    res_addres = default_address if default_address else os.getenv('DEFAULT_IP_ADDRESS') 
    res_port = default_port if default_port else os.getenv('DEFAULT_PORT') 
    parser = argparse.ArgumentParser(description='Server script')
    parser.add_argument('-a', default=res_addres, type=str, nargs='?', \
        help='Параметр -a позволяет указать IP-адрес, с которого будут приниматься соединения. (по умолчанию адрес не указан, ')
    parser.add_argument('-p', default=res_port, type=int, nargs='?', \
        help='Параметр -p позволяет указать порт сервера (по умолчанию 7777)')
    parser.add_argument('--no_gui', action='store_true')
    
    args = parser.parse_args(sys.argv[1:])
    serv_addr = args.a
    listen_port = args.p
    gui_flag = args.no_gui
    return serv_addr, listen_port, gui_flag


def config_load():
    """ Загрузка файла конфигурации """
    config = configparser.ConfigParser()
    dir_path = os.getcwd()
    config.read(f"{dir_path}/{'server.ini'}")
    # Если конфиг файл загружен правильно, запускаемся, иначе конфиг по умолчанию.
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', os.getenv('DEFAULT_PORT'))
        config.set('SETTINGS', 'Listen_Address', os.getenv('DEFAULT_IP_ADDRESS'))
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_chat.db3')
        return config        


def main():
    '''Основная функция'''
    load_dotenv()
   
    # Загрузка файла конфигурации сервера
    config = config_load()
    # print(f"///SERV_main_0: , "
    #     f"{os.path.join(config['SETTINGS']['Database_path'], config['SETTINGS']['Database_file'])}," 
    #     f"{config['SETTINGS']['Default_port']} == {type(config['SETTINGS']['Listen_Address'])}"
    #     f"{config['SETTINGS']['Listen_Address']}  ")

    # Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
    serv_addr, listen_port, gui_flag = srv_args_parser(
        config['SETTINGS']['Listen_Address'], config['SETTINGS']['Default_port'])


    # Инициализация базы данных
    path_to_db = os.path.join(
            config['SETTINGS']['Database_path'],
            'server',
            config['SETTINGS']['Database_file'])
    print("///SERV_main_1: ",type("///SERV_main_1: "), ',',  path_to_db)
    database = ServerStorage(path_to_db)
    print("///SERV_main_2: ", database)
    
    # Создание экземпляра класса - сервера и его запуск:
    server = Server(serv_addr, listen_port, database)
    server.daemon = True
    server.start()
    print("///SERV_main_3")


    # Если  указан параметр без GUI то запускаем простенький обработчик
    # консольного ввода
    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                # Если выход, то завршаем основной цикл сервера.
                server.running = False
                server.join()
                break

    # Если не указан запуск без GUI, то запускаем GUI:
    else:
        # Создаём графическое окуружение для сервера:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)

        # Инициализируем параметры в окна
        main_window.statusBar().showMessage(
            f"Server Working.    Server address: {serv_addr}. Server port: {listen_port}")

        # Запускаем GUI
        server_app.exec_()

        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    main()
