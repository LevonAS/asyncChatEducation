import dis


# Метакласс для проверки Server
class ServerMaker(type):
    def __init__(self, clsname, bases, dct):
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
                    # opname - имя для операции
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            # заполняем список методами, использующимися в функциях класса
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs.append(i.argval)

        print('// Методы модуля Server:', methods)
        print('// Атрибуты модуля Server:', attrs)

        # Если обнаружено использование недопустимого метода connect, бросаем исключение:
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        # Если сокет не инициализировался константами SOCK_STREAM(TCP) AF_INET(IPv4), тоже исключение.
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета! Использованы параметры не TCP/IP протокола')
        # Обязательно вызываем конструктор предка
        super().__init__(clsname, bases, dct)


# Метакласс для проверки корректности Client
class ClientMaker(type):
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
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(func)

        print('// Методы модуля Client:', methods)

        # Если обнаружено использование недопустимого метода accept, listen, socket бросаем исключение:
        for command in ('accept', 'listen'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода')
        # Вызов get_message или send_message из utils считаем корректным использованием сокетов
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        # Обязательно вызываем конструктор предка
        super().__init__(clsname, bases, dct)