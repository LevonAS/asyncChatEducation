import os, sys, json, select, time, argparse, socket
# from socket import socket, AF_INET, SOCK_STREAM
from dotenv import load_dotenv
import logging
import log.server_log_config
from log.decor_log import log
# from utils import get_message, send_message
# from utils import Utils
# from metaclasses import ServerVerifier
# from descriptors import DescriptorAddress, DescriptorPort
from utils import DescriptorAddress, DescriptorPort, ServerVerifier


class Server(metaclass=ServerVerifier):
    # utils = Utils()
    serv_addr = DescriptorAddress()
    listen_port = DescriptorPort()

    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SERVER_LOGGER = logging.getLogger('server')
        # Очередь ожидающих клиентов
        self.clients = []
        # Очередь сообщений
        self.messages = []
        # Словарь, содержащий имена пользователей и соответствующие им сокеты
        self.names = {}

        self.run()


    @log
    def send_message(self, open_socket, message):
        json_message = json.dumps(message)
        response = json_message.encode(os.getenv('ENCODING'))
        open_socket.send(response)
        # print("SERV_SM_1", "[message:]", message, "\n[response:]", response, "\n[open_socket:]", open_socket, "\n")

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
    def process_client_message(self, message, messages_list, client, clients, names):
        """
        Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости.
        :param os.getenv('MESSAGE'):
        :param messages_list:
        :param client:
        :param clients:
        :param names:
        :return:
        """
        
        self.SERVER_LOGGER.debug(f"Разбор сообщения от клиента : {message}")
        # print("SERV_PCM1 [names:]", names, "\n[message:]", message)
        # Если это сообщение о присутствии, принимаем и отвечаем
        if os.getenv('ACTION') in message \
                    and message[os.getenv('ACTION')] == os.getenv('PRESENCE') \
                    and os.getenv('TIME') in message \
                    and os.getenv('USER') in message:
            # Если такой пользователь ещё не зарегистрирован,
            # регистрируем, иначе отправляем ответ и завершаем соединение.
            # print("SERV_PCM2 [names:]", names, "\n[message:]", message)
            if message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')] not in names.keys():
                names[message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')]] = client
                # print("SERV_PCM3", "[names:]", names, "\n[message:]", message)
                self.send_message(client, {os.getenv('RESPONSE'): 200})
            else:
                self.send_message(client, {
                    os.getenv('RESPONSE'): 409,
                    os.getenv('ERROR'): 'Username already in use.'
                })
                clients.remove(client)
                # client.close()       
                return
        # Если это сообщение, то добавляем его в очередь сообщений.
        # Ответ не требуется.
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('MESSAGE') \
                and os.getenv('DESTINATION') in message \
                and os.getenv('TIME') in message \
                and os.getenv('SENDER') in message \
                and os.getenv('MESSAGE_TEXT') in message:
            messages_list.append(message)
            return
        # Отправляем по запросу список пользователей подключённых к серверу
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('GETULIST') \
                and os.getenv('TIME') in message \
                and os.getenv('USER') in message:
            # print("SERV_GUL1 [names:]", names)
            # print(list(names.keys()))
            # print(' '.join(list(names.keys())))
            users = ' '.join(list(names.keys()))
            self.send_message(client, {
                os.getenv('ACTION'): os.getenv('GETULIST'),
                os.getenv('USERS_LIST'): users
            })
            return
        # Если клиент выходит
        elif os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('EXIT') \
                and os.getenv('ACCOUNT_NAME') in message:
            clients.remove(names[message[os.getenv('ACCOUNT_NAME')]])
            names[message[os.getenv('ACCOUNT_NAME')]].close()
            del names[message[os.getenv('ACCOUNT_NAME')]]
            return
        # Иначе отдаём Bad request
        else:
            response = os.getenv('RESPONSE_400')
            response[os.getenv('ERROR')] = 'Bad request.'
            self.send_message(client, response)
            return

    @log
    def process_message(self, message, names, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь-сообщение,
        список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
        :param os.getenv('MESSAGE'):
        :param names:
        :param listen_socks:
        :return:
        """
        if message[os.getenv('DESTINATION')] in names \
                and names[message[os.getenv('DESTINATION')]] in listen_socks:
            self.send_message(names[message[os.getenv('DESTINATION')]], message)
            self.SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[os.getenv("DESTINATION")]} '
                        f'от пользователя {message[os.getenv("SENDER")]}.')
        elif message[os.getenv('DESTINATION')] in names \
                and names[message[os.getenv('DESTINATION')]] not in listen_socks:
            raise ConnectionError
        else:
            self.SERVER_LOGGER.os.getenv('ERROR')(
                f'Пользователь {message[os.getenv("DESTINATION")]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    @log
    def get_args_parser(self):
        """
        Парсер аргументов коммандной строки
        """
        parser = argparse.ArgumentParser(description='Server script')
        parser.add_argument('-a', default=os.getenv('DEFAULT_IP_ADDRESS'), type=str, nargs='?', \
            help='Параметр -a позволяет указать IP-адрес, с которого будут приниматься соединения. (по умолчанию адрес не указан, ')
        parser.add_argument('-p', default=os.getenv('DEFAULT_PORT'), type=int, nargs='?', \
            help='Параметр -p позволяет указать порт сервера (по умолчанию 7777)')
        return parser

    @log
    def get_addr_port(self):
        """
        Определяем порт, на котором будет работать сервер, и адрес с которого будут поступать запросы на сервер.
        По умолчанию сервер будет принимать со всех адресов.
        """
        parser = self.get_args_parser()
        args = parser.parse_args(sys.argv[1:])
        self.serv_addr = args.a
        self.listen_port = args.p


    def start_server(self):
        load_dotenv()

        self.get_addr_port()

        self.SERVER_LOGGER.info(
            f'Консольный месседжер. Серверный модуль запущен.\n'
            f'Адрес: {self.serv_addr} Порт: {self.listen_port}\n'
            f'Для выхода нажмите CTRL+C\n')
        print( f'Консольный месседжер. Серверный модуль запущен.\n'
            f'Адрес: {self.serv_addr} Порт: {self.listen_port}\n'
            f'Для выхода нажмите CTRL+C\n')

        self.s.bind((self.serv_addr, int(self.listen_port)))
        self.s.listen(int(os.getenv('MAX_CONNECTIONS')))
        self.s.settimeout(0.2) # Таймаут для операций с сокетом

        
        while True:
            try:
                client_sock, client_address = self.s.accept()
            except OSError:
                pass # timeout вышел
            else:
                self.SERVER_LOGGER.info(f'Получен запрос на соединение от {client_address}')
                self.clients.append(client_sock)
            finally:
                rlist = [] #список объектов, по готовности из которых нужно что-то прочитать
                wlist = [] #список объектов, по готовности в которые нужно что-то записать
                err_lst = [] #список объектов, в которых возможно будут ошибки
            
            # Проверка на наличие ждущих клиентов
            try:
                if self.clients:
                    rlist, wlist, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass
            
            # print("SERV_1 |||", "[rlist:]", rlist, "\n[wlist:]", wlist, "\n[names:]", names, "\n[messages:]", messages, "\n")
            # принимаем сообщения и если там есть сообщения,
            # кладём в словарь, если ошибка, исключаем клиента.
            if rlist:
                for client_with_message in rlist:
                    try:
                        self.process_client_message(self.get_message(client_with_message),
                                    self.messages, client_with_message, self.clients, self.names)
                    except Exception:
                        self.SERVER_LOGGER.info(f'Отправляющий клиент '
                            f'{client_with_message.getpeername()} отключился от сервера.')
                        print(f'Отправляющий клиент '
                            f'{client_with_message.getpeername()} отключился от сервера.')
                        self.clients.remove(client_with_message)
            
            # print("SERV_2 |||", "[rlist:]", rlist, "\n[wlist:]", wlist, "\n[names:]", self.names, "\n[messages:]", self.messages, "\n")
            # Если есть сообщения, обрабатываем каждое.
            for i in self.messages:
                try:
                    # print("SERV_3 |||","[names:]", self.names, "\n[i:]", i)
                    self.process_message(i, self.names, wlist)
                except Exception:
                    self.SERVER_LOGGER.info(f'Связь с клиентом с именем '
                        f'{i[os.getenv("DESTINATION")]} была потеряна при отправке сообщения')
                    print(f'Связь с клиентом с именем '
                        f'{i[os.getenv("DESTINATION")]} была потеряна при отправке сообщения')
                    self.clients.remove(self.names[i[os.getenv('DESTINATION')]])
                    del self.names[i[os.getenv('DESTINATION')]]
            self.messages.clear()    
        
    
    def run(self):
        self.start_server()    

if __name__ == '__main__':
    server = Server()
    