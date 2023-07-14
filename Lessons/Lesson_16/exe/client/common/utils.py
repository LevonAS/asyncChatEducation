import os
import sys
import time
import json
import dis
import logging
from log.decor_log import log
from ipaddress import ip_address

"""
Модуль dis поддерживает анализ CPython байткода и его дизассемблирование
CPython байткод, принимаемый на входе этого модуля, определен в файле Include/opcode.h и используется компилятором и интерпретатором
https://habr.com/ru/companies/otus/articles/460143/
https://digitology.tech/docs/python_3/library/dis.html#:~:text=%D0%9C%D0%BE%D0%B4%D1%83%D0%BB%D1%8C%20dis%20%D0%BF%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B8%D0%B2%D0%B0%D0%B5%D1%82%20%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7%20CPython,%D1%8F%D0%B2%D0%BB%D1%8F%D0%B5%D1%82%D1%81%D1%8F%20%D0%B4%D0%B5%D1%82%D0%B0%D0%BB%D0%B8%D0%B7%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D0%BE%D0%B9%20%D1%80%D0%B5%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D0%B5%D0%B9%20CPython%20%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D0%BF%D1%80%D0%B5%D1%82%D0%B0%D1%82%D0%BE%D1%80%D0%B0.
https://habr.com/ru/articles/145835/
"""

SERVER_LOGGER = logging.getLogger('server')


class Utils():
    def __init__(self):
        pass

    @log
    def send_message(self, open_socket, message):
        json_message = json.dumps(message)
        response = json_message.encode(os.getenv('ENCODING'))
        open_socket.send(response)
        # print("UUU_SM_1", "[message:]", message, "\n[response:]", response, "\n[open_socket:]", open_socket, "\n")

    @log
    def get_message(self, client):
        """
        Утилита приёма и декодирования сообщения принимает байты выдаёт словарь,
        если приняточто-то другое отдаёт ошибку значения
        :param client:
        :return:
        """
        response = client.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
        # print("UUU_GM_1", response, "||||")
        if isinstance(response, bytes):
            json_response = response.decode(os.getenv('ENCODING'))
            response_dict = json.loads(json_response)
            if isinstance(response_dict, dict):
                # print("UUU_GM_2", response_dict, "||||")
                return response_dict
            raise ValueError
        raise ValueError


class DescriptorAddress:
    """ Проверяет ip адрес, если он указан в параметрах """

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        # Если адрес указан
        if value:
            try:
                address = ip_address(value)
            except ValueError:
                SERVER_LOGGER.critical(
                    f"/D/!!!При запуске указан некорректный ip-адрес: {value}")
                sys.exit(1)
        instance.__dict__[self.name] = value


class DescriptorPort:
    """
    Проверяет номер порта.
    Если успешно, то номер порта устанавливается указанным в параметре -p
    Иначе устанавливается номер дефолтного значения порта (7777)
    """

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        # Если порт указан не корректно, устанавливаем его значение в 7777
        if not 1023 < value < 65536:
            SERVER_LOGGER.critical(
                f"/D/!!!Попытка запуска с указанием неподходящего значения порта {value}. Допустимы адреса с 1024 до 65535. "
                f"Порту принудительно присвоено значение по умолчанию: {os.getenv('DEFAULT_PORT')}")
            # Если порт не прошел проверку, добавляем его в список атрибутов экземпляра и передаем ему значение 7777
            instance.__dict__[self.name] = int(os.getenv('DEFAULT_PORT'))
        else:
            # Если порт прошел проверку, добавляем его в список атрибутов экземпляра
            instance.__dict__[self.name] = value


class ServerVerifier(type):
    """ Метакласс для проверки модуля Server """
    def __init__(self, clsname, bases, dct):
        # clsname - ссылка на экземпляр Server
        # bases - кортеж базовых классов для Server - ()
        # dct - словарь атрибутов и методов экземпляра Server

        # Список для методов Server
        methods = []
        # Список для атрибутов Server
        attrs = []
        # перебираем ключи словаря атрибутов и методов Server
        for func in dct:
            try:
                # Возвращает итератор по инструкциям в предоставленной функции, методе, строке исходного кода или объекте кода
                ret = dis.get_instructions(dct[func])
                # Если не функция то ловим исключение
            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы и атрибуты.
                for i in ret:
                    # print(i)
                    # i - Instruction(opname='LOAD_GLOBAL', opcode=116, arg=9, argval='send_message',
                    # argrepr='send_message', offset=308, starts_line=201, is_jump_target=False)
                    # opname - имя для операции
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            # заполняем список методами, использующимися в функциях класса
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs.append(i.argval)

        # print('/M/ Методы модуля Server:', methods)
        # print('/M/ Атрибуты модуля Server:', attrs)

        # Если обнаружено использование недопустимого метода connect, бросаем исключение:
        if 'connect' in methods:
            raise TypeError(
                'Использование метода connect недопустимо в серверном классе')
        # Если сокет не инициализировался константами SOCK_STREAM(TCP) AF_INET(IPv4), тоже исключение.
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError(
                'Некорректная инициализация сокета! Использованы параметры не TCP/IP протокола')
        # Обязательно вызываем конструктор предка
        super().__init__(clsname, bases, dct)


class ClientVerifier(type):
    """ Метакласс для проверки корректности модуля Client """
    def __init__(self, clsname, bases, dct):
        # Список для методов objClient
        methods = []
        for func in dct:
            try:
                ret = dis.get_instructions(dct[func])
                # Если не функция то ловим исключение
            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы
                for i in ret:
                    # print(func)
                    # if func == 'send_message':
                    #     print(func, i.opname)
                    if i.opname == 'LOAD_GLOBAL':
                        # if func == 'send_message':
                        #     print(func, i.opname, i.argval)
                        if i.argval not in methods:
                            # methods.append(i.argval)
                            # i.argval - это не имя метода! Там никогда не будет send_message и get_message
                            methods.append(func)

        # print('/M/ Методы модуля Client:', methods)

        # Если обнаружено использование недопустимого метода accept, listen, socket бросаем исключение:
        for command in ('accept', 'listen'):
            if command in methods:
                raise TypeError(
                    'В классе обнаружено использование запрещённого метода')
        # Вызов get_message или send_message из utils считаем корректным использованием сокетов
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError(
                'Отсутствуют вызовы функций, работающих с сокетами.')
        # Обязательно вызываем конструктор предка
        super().__init__(clsname, bases, dct)
