from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
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
    name = Column('name', String, unique=True)
    last_login = Column('last_login', DateTime)
    passwd_hash = Column('passwd_hash', String)
    pubkey = Column('pubkey', Text)

    def __init__(self, name, passwd_hash):
        self.name = name
        self.last_login = datetime.datetime.now()
        self.passwd_hash = passwd_hash
        self.pubkey = None

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


class UsersContacts(BASE):
    """
    Модель таблицы контактов пользователей
    """
    __tablename__ = "UsersContacts"
    id = Column('id', Integer, primary_key=True)
    user = Column('user', ForeignKey('AllUsers.id'))
    contact = Column('contact', ForeignKey('AllUsers.id'))

    def __init__(self, user_id, contact):
        self.user = user_id
        self.contact = contact

    def __repr__(self):
        return f"UsersContacts (id={self.id}, user={self.user}, contact={self.contact}"


class UsersHistory(BASE):
    """
    Модель таблицы истории действий пользователей
    """
    __tablename__ = "UsersHistory"
    id = Column('id', Integer, primary_key=True)
    user = Column('user', ForeignKey('AllUsers.id'))
    sent = Column('sent', Integer)
    accepted = Column('accepted', Integer)

    def __init__(self, user_id):
        self.user = user_id
        self.sent = 0
        self.accepted = 0

    def __repr__(self):
        return f"UsersHistory (id={self.id}, user={self.user}, sent={self.sent}, accepted={self.accepted}"
