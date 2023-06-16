import os, sys, json, select, time
from socket import socket, AF_INET, SOCK_STREAM
from dotenv import load_dotenv
import logging
import log.server_log_config
from log.decor_log import log
from utils import get_message, send_message


#Инициализация логирования сервера.
SERVER_LOGGER = logging.getLogger('server')

@log
def process_client_message(message, messages_list, client, clients, names):
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
    
    SERVER_LOGGER.debug(f"Разбор сообщения от клиента : {message}")
    # print("SERV_PCM2 [names:]", names, "\n[message:]", message)
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
            send_message(client, {os.getenv('RESPONSE'): 200})
        else:
            send_message(client, {
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
        send_message(client, {
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
        send_message(client, response)
        return

@log
def process_message(message, names, listen_socks):
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
        send_message(names[message[os.getenv('DESTINATION')]], message)
        SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[os.getenv("DESTINATION")]} '
                    f'от пользователя {message[os.getenv("SENDER")]}.')
    elif message[os.getenv('DESTINATION')] in names \
            and names[message[os.getenv('DESTINATION')]] not in listen_socks:
        raise ConnectionError
    else:
        SERVER_LOGGER.os.getenv('ERROR')(
            f'Пользователь {message[os.getenv("DESTINATION")]} не зарегистрирован на сервере, '
            f'отправка сообщения невозможна.')


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
        print('Консольный месседжер. Серверный модуль запущен.')
    except ValueError:
        SERVER_LOGGER.critical(
            'В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)


    s = socket(AF_INET, SOCK_STREAM)
    s.bind((serv_addr, int(listen_port)))
    s.listen(int(os.getenv('MAX_CONNECTIONS')))
    s.settimeout(0.2) # Таймаут для операций с сокетом

    # список клиентов , очередь сообщений
    clients = []
    messages = []
    # Словарь, содержащий имена пользователей и соответствующие им сокеты.
    names = dict()
    
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
        
        # Проверка на наличие ждущих клиентов
        try:
            if clients:
                rlist, wlist, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass
        
        # print("SERV_1 |||", "[rlist:]", rlist, "\n[wlist:]", wlist, "\n[names:]", names, "\n[messages:]", messages, "\n")
        # принимаем сообщения и если там есть сообщения,
        # кладём в словарь, если ошибка, исключаем клиента.
        if rlist:
            for client_with_message in rlist:
                try:
                    process_client_message(get_message(client_with_message),
                                messages, client_with_message, clients, names)
                except Exception:
                    SERVER_LOGGER.info(f'Отправляющий клиент '
                        f'{client_with_message.getpeername()} отключился от сервера.')
                    print(f'Отправляющий клиент '
                        f'{client_with_message.getpeername()} отключился от сервера.')
                    clients.remove(client_with_message)
        
        # print("SERV_2 |||", "[rlist:]", rlist, "\n[wlist:]", wlist, "\n[names:]", names, "\n[messages:]", messages, "\n")
        # Если есть сообщения, обрабатываем каждое.
        for i in messages:
            try:
                # print("SERV_3 |||","[names:]", names, "\n[i:]", i)
                process_message(i, names, wlist)
            except Exception:
                SERVER_LOGGER.info(f'Связь с клиентом с именем '
                    f'{i[os.getenv("DESTINATION")]} была потеряна при отправке сообщения')
                print(f'Связь с клиентом с именем '
                    f'{i[os.getenv("DESTINATION")]} была потеряна при отправке сообщения')
                clients.remove(names[i[os.getenv('DESTINATION')]])
                del names[i[os.getenv('DESTINATION')]]
        messages.clear()    
        

if __name__ == '__main__':
    server()
    