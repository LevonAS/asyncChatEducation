"""Декораторы"""

import sys, logging, traceback, inspect, socket
from functools import wraps
# from dotenv import load_dotenv
# sys.path.append('../')

# метод определения модуля, источника запуска.
# Метод find () возвращает индекс первого вхождения искомой подстроки,
# если он найден в данной строке.
# Если его не найдено, - возвращает -1.
# os.path.split(sys.argv[0])[1]
if sys.argv[0].find('client') == -1:
    # если не клиент то сервер!
    LOGGER = logging.getLogger('server')
else:
    # ну, раз не сервер, то клиент
    LOGGER = logging.getLogger('client')


# Реализация в виде функции
def log(func_to_log):
    """Функция-декоратор"""
    def log_saver(*args, **kwargs):
        """Обертка"""
        ret = func_to_log(*args, **kwargs)
        LOGGER.debug(f'Из модуля "{func_to_log.__module__}" '
                     f'была вызвана функция "{func_to_log.__name__}" c параметрами {args}, {kwargs}. '
                     f'Инициатор вызова - "{inspect.stack()[1][3]}"', stacklevel=2)
        return ret
    return log_saver



def go():
    print("!!go!!!go!!!!")



# Реализация в виде класса
# class Log:
#     """Класс-декоратор"""
#     def __call__(self, func_to_log):
#         def log_saver(*args, **kwargs):
#             """Обертка"""
#             ret = func_to_log(*args, **kwargs)
#             LOGGER.debug(f'Из модуля "{func_to_log.__module__}" '
#                         f'была вызвана функция "{func_to_log.__name__}" c параметрами {args}, {kwargs}. '
#                         f'Инициатор вызова - "{inspect.stack()[1][3]}"', stacklevel=2)
#             return ret
#         return log_saver

def login_required(func):
    '''
    Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в
    списке авторизованных клиентов.
    За исключением передачи словаря-запроса
    на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError
    '''

    def checker(*args, **kwargs):
        # load_dotenv()
        
        # проверяем, что первый аргумент - экземпляр MessageProcessor
        # Импортить необходимо тут, иначе ошибка рекурсивного импорта.
        from server_run import Server
        print("///SERV_login_1 [args:]", args, "\n")
        if isinstance(args[0], Server):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    # MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            # Теперь надо проверить, что передаваемые аргументы не presence
            # сообщение. Если presense, то разрешаем
            for arg in args:
                if isinstance(arg, dict):
                    if os.getenv('ACTION') in arg \
                            and arg[os.getenv('ACTION')] == os.getenv('PRESENCE'):
                        found = True
            # Если не не авторизован и не сообщение начала авторизации, то
            # вызываем исключение.
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker