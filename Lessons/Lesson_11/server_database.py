from sqlalchemy import create_engine
# from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.orm import Session
# from sqlalchemy.ext.declarative import declarative_base
import os, datetime
from dotenv import load_dotenv
from models import BASE, AllUsers, ActiveUsers, LoginHistory



class ServerStorage:
    # load_dotenv()
    def __init__(self):
        # Создаём движок базы данных
        self.ENGINE = create_engine(os.getenv('SERVER_DATABASE'), echo=False, pool_recycle=7200)
        # Формирование таблиц
        BASE.metadata.create_all(self.ENGINE)
        # Создание сессии
        self.session = Session(bind=self.ENGINE)
        # Если в таблице активных пользователей есть записи, то их необходимо удалить
        # Когда устанавливаем соединение, очищаем таблицу активных пользователей
        self.session.query(ActiveUsers).delete()
        self.session.commit()
    
    
    def user_login(self, username, ip_address, port) -> None:
        """
        Метод, выполняющийся при входе пользователя, записывает в базу факт входа
        """
        # print(username, ip_address, port)
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        query = self.session.query(AllUsers).filter_by(name=username)
        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        if query.count():
            user = query.first()
            user.last_login = datetime.datetime.now()
        # Если нет, то создаздаём нового пользователя
        else:
            # Создаем экземпляр класса AllUsers, через который передаем данные в таблицу
            user = AllUsers(username)
            self.session.add(user)
            # Комит здесь нужен, чтобы присвоился ID
            self.session.commit()
        # print(user)

        # Теперь можно создать запись в таблицу активных пользователей о факте входа.
        # Создаем экземпляр класса ActiveUsers, через который передаем данные в таблицу
        new_active_user = ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        # и сохранить в историю входов
        # Создаем экземпляр класса LoginHistory, через который передаем данные в таблицу
        history = LoginHistory(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(history)

        # Сохраняем изменения
        self.session.commit()


    def user_logout(self, username) -> None:
        """
        Метод, фиксирующий отключение пользователя
        """
        # Запрашиваем пользователя, что покидает нас
        # получаем запись из таблицы AllUsers
        user = self.session.query(AllUsers).filter_by(name=username).first()

        # Удаляем его из таблицы активных пользователей.
        # Удаляем запись из таблицы ActiveUsers
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


    def login_history(self, username: str | None = None):
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
  
    
    # def create(self, uname):
    #     USER = AllUsers(name=uname)
    #     self.session.add(USER)
    #     # Комит здесь нужен, чтобы присвоился ID
    #     self.session.commit()
    #     # SESS_OBJ = self.session()
    #     # SESS_OBJ.add(USER)
    #     # # self.session.add(USER)
    #     # self.session.commit()
    #     print(USER)


# Отладка
if __name__ == '__main__':
    load_dotenv()
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