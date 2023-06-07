import sys, logging, logging.handlers, os.path

# project_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.append(project_directory)

# формировщик логов (formatter)
FORMATTER = logging.Formatter(
    "%(asctime)s - %(levelname)-10s - %(module)-10s - %(message)s ")

# задаём путь к папке/файлу с логом server.log
storage_name = './logs'
if not os.path.exists(storage_name):
    os.mkdir(storage_name)
filename = os.path.join(storage_name, 'server.log')

# потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)

FILE_HANDLER = logging.handlers.TimedRotatingFileHandler(
                filename, encoding='utf8', interval=1, when='midnight')
FILE_HANDLER.setFormatter(FORMATTER)

# регистратор
SERVER_LOGGER = logging.getLogger('server')
SERVER_LOGGER.addHandler(STREAM_HANDLER)
SERVER_LOGGER.addHandler(FILE_HANDLER)
SERVER_LOGGER.setLevel(logging.DEBUG)


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(FORMATTER)
    SERVER_LOGGER.addHandler(console)
    SERVER_LOGGER.critical('Тест логгера: критическая ошибка')
    SERVER_LOGGER.error('Тест логгера: ошибка')
    SERVER_LOGGER.warning('Тест логгера: предупреждения')
    SERVER_LOGGER.debug('Тест логгера: отладочная информация')
    SERVER_LOGGER.info('Тест логгера: информационное сообщение')
