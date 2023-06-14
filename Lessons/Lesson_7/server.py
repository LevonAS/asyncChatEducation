import os, sys, json, select, time
from socket import socket, AF_INET, SOCK_STREAM
from dotenv import load_dotenv
import logging
import log.server_log_config
from log.decor_log import log
from utils import get_message, send_message, process_client_message


#Инициализация логирования сервера.
SERVER_LOGGER = logging.getLogger('server')


def server():
    load_dotenv()
    global serv_addr, listen_port
    try:
        if sys.argv[1] == '-a' and sys.argv[3] == '-p':
            head, a, serv_addr, p, listen_port, *tail = sys.argv
            if int(listen_port) < 1024 or int(listen_port) > 65535:
                raise ValueError
            SERVER_LOGGER.info(
                  f'Сервер запущен!\n'
                  f'Адрес: {serv_addr} Порт: {listen_port}\n'
                  f'Для выхода нажмите CTRL+C\n')
        else:
            raise NameError
    except (IndexError, NameError):
        serv_addr = os.getenv('DEFAULT_IP_ADDRESS')
        listen_port = os.getenv('DEFAULT_PORT')
        SERVER_LOGGER.info(
              f'Сервер запущен с настройками по умолчанию!\n'
              f'Адрес: {serv_addr} Порт: {listen_port}\n'
              f'Для ручных настроек подключения используйте аргументы командной строки:\n'
              f'$ python server.py -a [ip-адрес] -p [порт сервера]\n\n'
              f'Для выхода нажмите CTRL+C\n')
    except ValueError:
        SERVER_LOGGER.critical(
            'В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)


    s = socket(AF_INET, SOCK_STREAM)
    s.bind((serv_addr, int(listen_port)))
    s.listen(int(os.getenv('MAX_CONNECTIONS')))
    s.settimeout(3) # Таймаут для операций с сокетом

    # список клиентов , очередь сообщений
    clients = []
    messages = []

    while True:
        try:
            client_sock, client_address = s.accept()
        except OSError:
            pass # timeout вышел
        else:
            SERVER_LOGGER.info(f'Получен запрос на соединение от {client_address}')
            clients.append(client_sock)
        finally:
            rlist = [] #список объектов, по готовности из которых нужно что-то прочитать
            wlist = [] #список объектов, по готовности в которые нужно что-то записать
            err_lst = [] #список объектов, в которых возможно будут ошибки
            # Проверяем на наличие ждущих клиентов
        try:
            if clients:
                rlist, wlist, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass
        
        # print("SERV_1", "[rlist:]", rlist, "\n[wlist:]", wlist, "\n[messages:]", messages)
        # принимаем сообщения и если там есть сообщения,
        # кладём в словарь, если ошибка, исключаем клиента.
        if rlist:
            for client_with_message in rlist:
                try:
                    process_client_message(get_message(client_with_message),
                                           messages, client_with_message)
                except:
                    SERVER_LOGGER.info(f'Отправляющий клиент '
                                f'отключился от сервера.')
                    print(f'Отправляющий клиент '
                                f'отключился от сервера.')
                    clients.remove(client_with_message)
        
        # print("SERV_2", "[rlist:]", rlist, "\n[wlist:]", wlist, "\n[messages:]", messages, "\n")
        # Если есть сообщения для отправки и ожидающие клиенты, отправляем им сообщение.
        if messages and wlist:
            message = {
                os.getenv('ACTION'): os.getenv('MESSAGE'),
                os.getenv('SENDER'): messages[0][0],
                os.getenv('TIME'): time.time(),
                os.getenv('MESSAGE_TEXT'): messages[0][1]
            }
            del messages[0]
            # print("SERV_3", "[wlist:]", wlist, "\n[message:]", message, "\n")
            for waiting_client in wlist:
                try:
                    send_message(waiting_client, message)
                except:
                    SERVER_LOGGER.info(f'Ожидающий клиент  отключился от сервера.')
                    clients.remove(waiting_client)


if __name__ == '__main__':
    server()
    