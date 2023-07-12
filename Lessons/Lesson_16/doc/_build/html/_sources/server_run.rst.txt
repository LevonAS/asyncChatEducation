Server module
=================================================

Модуль сервера мессенджера
Обрабатывает словари - сообщения, хранит публичные ключи клиентов

Использование:

Модуль подерживает аргементы командной стороки:

1. -p - Порт на котором принимаются соединения
2. -a - Адрес с которого принимаются соединения
3. --no_gui Запуск только основных функций, без графической оболочки

* В данном режиме поддерживается только 1 команда: exit - завершение работы

Примеры использования:

``python server_run.py -p 7777``

*Запуск сервера на порту 7777*

``python server_run.py -a localhost``

*Запуск сервера принимающего только соединения с localhost*

``python server_run.py --no-gui``

*Запуск без графической оболочки*


server_run.py
~~~~~~~~~

Модуль сервера, содержащий функционал инициализации приложения и парсер аргументов командной строки.
Принимает содинения, словари - пакеты от клиентов, обрабатывает поступающие сообщения.

server_run. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 3 элементов:

	* адрес с которого принимать соединения
	* порт
	* флаг запуска GUI

server_run. **config_load** ()
    Функция загрузки параметров конфигурации из ini файла.
    В случае отсутствия файла задаются параметры по умолчанию.

.. autoclass:: server_run.Server
	:members:


server_database.py
~~~~~~~~~~~

.. autoclass:: server.server_database.ServerStorage
	:members:

ui_server_main_window.py
~~~~~~~~~~~~~~

.. autoclass:: server.ui_server_main_window.MainWindow
	:members:

ui_add_user.py
~~~~~~~~~~~

.. autoclass:: server.ui_add_user.RegisterUser
	:members:

ui_remove_user.py
~~~~~~~~~~~~~~

.. autoclass:: server.ui_remove_user.DelUserDialog
	:members:

ui_config_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.ui_config_window.ConfigWindow
	:members:

ui_stat_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.ui_stat_window.StatWindow
	:members: