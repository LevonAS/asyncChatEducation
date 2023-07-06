"""
1. Реализовать аутентификацию пользователей на сервере.
2. Реализовать декоратор @login_required, проверяющий авторизованность пользователя для
   выполнения той или иной функции.
3. Реализовать хранение паролей в БД сервера (пароли не хранятся в открытом виде —
   хранится хэш-образ от пароля с добавлением криптографической соли).
4. * Реализовать возможность сквозного шифрования сообщений (использовать асимметричный
   шифр, ключи которого хранятся только у клиентов).
"""