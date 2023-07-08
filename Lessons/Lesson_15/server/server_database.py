import os, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import default_comparator
# from dotenv import load_dotenv
from server.server_models import BASE, AllUsers, ActiveUsers, LoginHistory, UsersContacts, UsersHistory



class ServerStorage:
    '''
    Класс - набор методов для работы с базой данных сервера.
    Использует SQLite базу данных, реализован с помощью SQLAlchemy ORM.
    '''
    # load_dotenv()
    def __init__(self, path):
        # Создаём движок базы данных
        self.ENGINE = create_engine(f'sqlite:///{path}', 
                                    echo=False, 
                                    pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        # Формирование таблиц
        BASE.metadata.create_all(self.ENGINE)
        # Создание сессии
        self.session = Session(bind=self.ENGINE)
        # Если в таблице активных пользователей есть записи, то их необходимо удалить
        # Когда устанавливаем соединение, очищаем таблицу активных пользователей
        self.session.query(ActiveUsers).delete()
        self.session.commit()
    
    
    def user_login(self, username, ip_address, port, key) -> None:
        """
        Метод выполняющийся при входе пользователя, записывает в базу факт входа
        Обновляет открытый ключ пользователя при его изменении.
        """
        # Запрос в таблицу пользователей на наличие там пользователя с таким
        # именем
        rez = self.session.query(AllUsers).filter_by(name=username)

        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        # и проверяем корректность ключа. Если клиент прислал новый ключ,
        # сохраняем его.
        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        # Если нету, то генерируем исключение
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        # Теперь можно создать запись в таблицу активных пользователей о факте
        # входа.
        new_active_user = ActiveUsers(
            user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        # и сохранить в историю входов
        history = LoginHistory(
            user.id, ip_address, port, datetime.datetime.now())
        self.session.add(history)

        # Сохрраняем изменения
        self.session.commit()

    def add_user(self, name, passwd_hash):
        '''
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        '''
        user_row = AllUsers(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = UsersHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        '''Метод удаляющий пользователя из базы.'''
        user = self.session.query(AllUsers).filter_by(name=name).first()
        self.session.query(ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(LoginHistory).filter_by(user=user.id).delete()
        self.session.query(UsersContacts).filter_by(user=user.id).delete()
        self.session.query(UsersContacts).filter_by(contact=user.id).delete()
        self.session.query(UsersHistory).filter_by(user=user.id).delete()
        self.session.query(AllUsers).filter_by(name=name).delete()
        self.session.commit()

    def get_hash(self, name):
        '''Метод получения хэша пароля пользователя.'''
        user = self.session.query(AllUsers).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        '''Метод получения публичного ключа пользователя.'''
        user = self.session.query(AllUsers).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        '''Метод проверяющий существование пользователя.'''
        if self.session.query(AllUsers).filter_by(name=name).count():
            return True
        else:
            return False


    def user_logout(self, username) -> None:
        """
        Метод, фиксирующий отключение пользователя
        """
        # Запрашиваем пользователя, что покидает нас
        user = self.session.query(AllUsers).filter_by(name=username).first()

        # Удаляем его из таблицы активных пользователей.
        self.session.query(ActiveUsers).filter_by(user=user.id).delete()

        # Применяем изменения
        self.session.commit()


    def users_list(self):
        """
        Метод возвращает список известных пользователей со временем последнего входа
        """
        query = self.session.query(
            AllUsers.name,
            AllUsers.last_login,
        )
        # Возвращаем список кортежей
        # print(query.all()[0][1].strftime('%Y-%m-%d %H:%M:%S'))
        return query.all()
    
   
    def active_users_list(self):
        """
        Метод возвращает список активных пользователей
        """
        # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время.
        query = self.session.query(
            AllUsers.name,
            ActiveUsers.ip_address,
            ActiveUsers.port,
            ActiveUsers.login_time
        ).join(AllUsers)
        # Возвращаем список кортежей
        # print(query.all())
        return query.all()


    def login_history(self, username=None):
        """
        Метод, возвращающий историю входов по пользователю или всех пользователей
        """
        # Запрашиваем историю входа
        query = self.session.query(AllUsers.name,
                                   LoginHistory.ip_address,
                                   LoginHistory.port,
                                   LoginHistory.date_time
                                   ).join(AllUsers)
        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(AllUsers.name == username)
        return query.all()


    def process_message(self, sender, recipient):
        '''Метод записывающий в таблицу статистики факт передачи сообщения.'''
        # Получаем ID отправителя и получателя
        sender = self.session.query(AllUsers).filter_by(name=sender).first().id
        recipient = self.session.query(AllUsers).filter_by(name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

        
    def add_contact(self, user, contact):
        """
        Метод добавляет контакт для пользователя
        """
        # Получаем ID пользователей
        user = self.session.query(AllUsers).filter_by(name=user).first()
        contact = self.session.query(AllUsers).filter_by(name=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю
        # пользователь мы доверяем)
        if not contact or self.session.query(
                UsersContacts).filter_by(
                user=user.id,
                contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        contact_row = UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    
    def remove_contact(self, user, contact):
        """
        Метод удаления контакта пользователя
        """
        # Получаем ID пользователей
        user = self.session.query(AllUsers).filter_by(name=user).first()
        contact = self.session.query(AllUsers).filter_by(name=contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы
        # доверяем)
        if not contact:
            return

        # Удаляем требуемое
        self.session.query(UsersContacts).filter(
            UsersContacts.user == user.id,
            UsersContacts.contact == contact.id
        ).delete()
        self.session.commit()

    
    def get_contacts(self, username):
        """
        Метод возвращает список контактов пользователя
        """
        # Запрашивааем указанного пользователя
        user = self.session.query(AllUsers).filter_by(name=username).one()

        # Запрашиваем его список контактов
        query = self.session.query(UsersContacts, AllUsers.name). \
            filter_by(user=user.id). \
            join(AllUsers, UsersContacts.contact == AllUsers.id)

        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]

    
    def message_history(self):
        """
        Метод возвращает количество переданных и полученных сообщений
        """
        query = self.session.query(
            AllUsers.name,
            AllUsers.last_login,
            UsersHistory.sent,
            UsersHistory.accepted
        ).join(AllUsers)
        # Возвращаем список кортежей
        return query.all()
  

# Отладка
if __name__ == '__main__':
    # load_dotenv()
    test_db = ServerStorage()
    # выполняем 'подключение' пользователя
    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)
    # выводим список кортежей - активных пользователей
    print("///active_users_list_1: ", test_db.active_users_list())
    # выполянем 'отключение' пользователя
    test_db.user_logout('client_1')
    # выводим список активных пользователей
    print("///active_users_list_2: ", test_db.active_users_list())
    # запрашиваем историю входов по пользователю
    test_db.login_history('client_1')
    # выводим список известных пользователей
    print("///users_list: ", test_db.users_list())
    # print("///message_history: ", test_db.active_users_list())