import sys
import os.path
import logging
import logging.handlers

# формировщик логов (formatter)
FORMATTER = logging.Formatter(
    "%(asctime)s - %(levelname)-10s - %(module)-10s - %(message)s ")

# задаём путь к папке/файлу с логом client.log
storage_name = './lib/log/logs'
# print("333", os.path.join(storage_name, 'client.log'))
if not os.path.exists(storage_name):
    os.mkdir(storage_name)
filename = os.path.join(storage_name, 'client.log')

# потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)

FILE_HANDLER = logging.FileHandler(filename, encoding='utf-8')
FILE_HANDLER.setFormatter(FORMATTER)

# регистратор
CLIENT_LOGGER = logging.getLogger('client')
CLIENT_LOGGER.addHandler(STREAM_HANDLER)
CLIENT_LOGGER.addHandler(FILE_HANDLER)
CLIENT_LOGGER.setLevel(logging.DEBUG)


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(FORMATTER)
    CLIENT_LOGGER.addHandler(console)
    CLIENT_LOGGER.critical('Тест логгера: критическая ошибка')
    CLIENT_LOGGER.error('Тест логгера: ошибка')
    CLIENT_LOGGER.warning('Тест логгера: предупреждения')
    CLIENT_LOGGER.debug('Тест логгера: отладочная информация')
    CLIENT_LOGGER.info('Тест логгера: информационное сообщение')
