from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
# from sqlalchemy.orm import  sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime


BASE = declarative_base()


class KnownUsers(BASE):
    """
    Модель таблицы известных пользователей чата
    """
    __tablename__ = 'knownUsers'
    id = Column('id', Integer, primary_key=True)
    username = Column('username', String)

    def __init__(self, user):
        self.id = None
        self.username = user

    
    def __str__(self) -> str:
        return f"KnownUsers (id={self.id}, username={self.username})"

    def __repr__(self) -> str:
        return str(self)


class MessageHistory(BASE):
    """
    Модель таблицы истории сообщений
    """
    __tablename__ = "messageHistory"
    id = Column('id', Integer, primary_key=True)
    from_user = Column('from_user', String)
    to_user = Column('to_user', String)
    message = Column('message', Text)
    date = Column('date', DateTime)


    def __init__(self, from_user, to_user, message):
        self.from_user = from_user
        self.to_user = to_user
        self.message = message
        self.date = datetime.datetime.now()


    def __repr__(self):
        return f"MessageHistory (id={self.id}, from_user={self.from_user}, to_user={self.to_user},\
          message={self.message}, date={self.date.strftime('%Y-%m-%d %H:%M:%S')})"


class Contacts(BASE):
    """
    Модель таблицы  контактов
    """
    __tablename__ = "contacts"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, unique=True)

    def __init__(self, contact):
        self.id = None
        self.name = contact


    def __repr__(self):
                return f"Contacts (id={self.id}, name={self.name})"

