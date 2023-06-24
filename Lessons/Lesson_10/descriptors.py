import logging
from ipaddress import ip_address


SERVER_LOGGER = logging.getLogger('server')


class DescriptorAddress:
    """
    Проверяет ip адрес, если он указан в параметрах
    """
    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        # Если адрес указан
        if value:
            try:
                address = ip_address(value)
            except ValueError:
                SERVER_LOGGER.critical(f'Для сервера указан не корректный ip-адрес: {value}')
                exit(1)
        instance.__dict__[self.name] = value


class DescriptorPort:
    """
    Проверяет номер порта.
    Если успешно, то номер порта устанавливается указанным в параметре -p
    Иначе устанавливается номер порта 7777
    """
    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        # Если порт указан не корректно, устанавливаем его значение в 7777
        if not 1023 < value < 65536:
            SERVER_LOGGER.critical(
                f'!!!Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535.')
            # Если порт не прошел проверку, добавляем его в список атрибутов экземпляра и передаем ему значение 7777
            instance.__dict__[self.name] = 7777
        else:
            # Если порт прошел проверку, добавляем его в список атрибутов экземпляра
            instance.__dict__[self.name] = value