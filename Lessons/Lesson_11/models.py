from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
# from sqlalchemy.orm import  sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime



BASE = declarative_base()


class AllUsers(BASE):
    """
    Модель таблицы всех пользователей чата
    """
    __tablename__ = 'AllUsers'
    id = Column('id', Integer, primary_key=True)
    # name = Column('name', String)
    name = Column('name', String, unique=True)
    last_login = Column('last_login', DateTime)

    def __init__(self, name):
        self.name = name
        self.last_login = datetime.datetime.now()

    # def __repr__(self):
    #     return f'<User({self.name}, {self.last_login})>'
    
    def __str__(self) -> str:
        return f"User (id={self.id}, name={self.name},\
          last_login={self.last_login.strftime('%Y-%m-%d %H:%M:%S')})"

    def __repr__(self) -> str:
        return str(self)


class ActiveUsers(BASE):
    """
    Модель таблицы текущих активных пользователей чата
    """
    __tablename__ = "active_users"
    id = Column('id', Integer, primary_key=True)
    # user = Column('user', ForeignKey('AllUsers.id'))
    user = Column('user', ForeignKey('AllUsers.id'), unique=True)
    ip_address = Column('ip_address', String)
    port = Column('port', Integer)
    login_time = Column('login_time', DateTime)


    def __init__(self, user_id, ip_address, port, login_time):
        self.user = user_id
        self.ip_address = ip_address
        self.port = port
        self.login_time = login_time


    def __repr__(self):
        return f"ActiveUsers (id={self.id}, user={self.user}, ip_address={self.ip_address},\
          port={self.port}, login_time={self.login_time.strftime('%Y-%m-%d %H:%M:%S')})"



class LoginHistory(BASE):
    """
    Модель таблицы истории входов
    """
    __tablename__ = "login_history"
    id = Column('id', Integer, primary_key=True)
    user = Column('user', ForeignKey('AllUsers.id'))
    ip_address = Column('ip_address', String)
    port = Column('port', Integer)
    date_time = Column('date_time', DateTime)


    def __init__(self, user_id, ip_address, port, date_time):
        self.user = user_id
        self.ip_address = ip_address
        self.port = port
        self.date_time = date_time


    def __repr__(self):
                return f"LoginHistory (id={self.id}, user={self.user}, ip_address={self.ip_address},\
             port={self.port}, date_time={self.date_time.strftime('%Y-%m-%d %H:%M:%S')})"

