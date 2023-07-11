import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import default_comparator
# from dotenv import load_dotenv
from client.client_models import BASE, KnownUsers, MessageStat, Contacts


class ClientDatabase:
    '''
    Класс - набор методов для работы с базой данных клиента.
    Использует SQLite базу данных, реализован с помощью SQLAlchemy ORM.
    '''
    # load_dotenv()

    def __init__(self, name):
        # Создаём движок базы данных, поскольку разрешено несколько клиентов одновременно, каждый должен иметь свою БД
        # Поскольку клиент мультипоточный необходимо отключить проверки на подключения с разных потоков,
        # иначе sqlite3.ProgrammingError
        print("///CLN_DB_1", name, f'sqlite:///client_chat_{name}.db3')
        self.database_engine = create_engine(f'sqlite:///client/client_chat_{name}.db3',
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        # Создаём таблицы
        BASE.metadata.create_all(bind=self.database_engine)

        # Создаём сессию
        self.session = Session(bind=self.database_engine)

        # Необходимо очистить таблицу контактов, т.к. при запуске они подгружаются с сервера.
        self.session.query(Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """ Метод добавления контактов """
        if not self.session.query(Contacts).filter_by(name=contact).count():
            contact_row = Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        """ Метод удаления контакта """
        self.session.query(Contacts).filter_by(name=contact).delete()

    def contacts_clear(self):
        '''Метод очищающий таблицу со списком контактов.'''
        self.session.query(Contacts).delete()

    def add_users(self, users_list):
        """
        Метод добавления известных пользователей.
        Пользователи получаются только с сервера, поэтому таблица очищается.
        """
        self.session.query(KnownUsers).delete()
        for user in users_list:
            user_row = KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, contact, direction, message):
        """ Метод сохраняющяя сообщения """
        message_row = MessageStat(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        """ Метод возвращающий контакты """
        return [contact[0] for contact in self.session.query(Contacts.name).all()]

    def get_users(self):
        """ Метод возвращающий список известных пользователей """
        return [user[0] for user in self.session.query(KnownUsers.username).all()]

    def check_user(self, user):
        """ Метод проверяющий наличие пользователя в известных """
        if self.session.query(KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        """ Метод проверяющий наличие пользователя в контактах """
        if self.session.query(Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, contact):
        """ Метод возвращающий историю переписки с определённым пользователем."""
        query = self.session.query(MessageStat).filter_by(contact=contact)
        return [(history_row.contact,
                 history_row.direction,
                 history_row.message,
                 history_row.date) for history_row in query.all()]


# отладка
if __name__ == '__main__':
    # load_dotenv()
    test_db = ClientDatabase('test1')
    # for i in ['test3', 'test4', 'test5']:
    #     test_db.add_contact(i)
    # test_db.add_contact('test4')
    # test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    # test_db.save_message('test1', 'test2', f'Привет! я тестовое сообщение от {datetime.datetime.now()}!')
    # test_db.save_message('test2', 'test1', f'Привет! я другое тестовое сообщение от {datetime.datetime.now()}!')
    # print('//Список контактов: ', test_db.get_contacts())
    # print('//Список известных пользователей: ', test_db.get_users())
    # print('//Проверка наличия пользователя test1 в известных: ', test_db.check_user('test1'))
    # print('//Проверка наличия пользователя test0 в известных: ', test_db.check_user('test10'))
    print(
        f"//История всех сообщений с участием пользователя test2:  {sorted(test_db.get_history('test2') , key=lambda item: item[3])} \n")
    # print(f"//История сообщений отосланных пользователю test2:  {test_db.get_history(to_who='test2')} \n")
    # print('//История переписки пользователя test3: ', test_db.get_history('test3'))
    # test_db.del_contact('test4')
    # print('//Список контактов, после удаленияиз него  одного контакта test4: ', test_db.get_contacts())
