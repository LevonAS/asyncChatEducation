Client module documentation
=================================================

Клиентское приложение для обмена сообщениями
Поддерживает отправку сообщений пользователям которые находятся в сети, сообщения шифруются
с помощью алгоритма RSA с длинной ключа 2048 bit

Поддерживает аргументы коммандной строки:

``python client_run.py {имя сервера} {порт} -n или --name {имя пользователя} -p или -password {пароль}``

1. {имя сервера} - адрес сервера сообщений
2. {порт} - порт по которому принимаются подключения
3. -n или --name - имя пользователя с которым произойдёт вход в систему
4. -p или --password - пароль пользователя

Все опции командной строки являются необязательными, но имя пользователя и пароль необходимо обязательно использовать в паре

Примеры использования:

* ``python client_run.py``

*Запуск приложения с параметрами по умолчанию.*

* ``python client_run.py ip_address some_port``

*Запуск приложения с указанием подключаться к серверу по адресу ip_address:port*

* ``python client_run.py -n test1 -p 123456``

*Запуск приложения с пользователем test1 и паролем 123456*

* ``python client_run.py ip_address some_port -n test1 -p 123456``

*Запуск приложения с пользователем test1 и паролем 123456 и указанием подключаться к серверу по адресу ip_address:port*


client_run.py
~~~~~~~~~

Запускаемый модуль, содержит функционал инициализации приложения, функционал реализующий транспортную подсистему, а также парсер переданных аргументов командной строки

client_run. **client_args_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов:

	* адрес сервера
	* порт
	* имя пользователя
	* пароль

    Выполняет проверку на корректность номера порта

.. autoclass:: client_run.Client
	:members:

client_database.py
~~~~~~~~~~~~~~

.. autoclass:: client.client_database.ClientDatabase
	:members:

client_main_window.py
~~~~~~~~~~~~~~

.. autoclass:: client.client_main_window.ClientMainWindow
	:members:

ui_start_dialog.py
~~~~~~~~~~~~~~~

.. autoclass:: client.ui_start.UserNameDialog
	:members:


ui_add_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client.ui_add_contact.AddContactDialog
	:members:


ui_del_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client.ui_del_contact.DelContactDialog
	:members: