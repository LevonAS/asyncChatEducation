import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base


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


class MessageStat(BASE):
    """
    Модель таблицы истории сообщений
    """
    __tablename__ = "messageStat"
    id = Column('id', Integer, primary_key=True)
    contact= Column('contact', String)
    direction = Column('direction', String)
    message = Column('message', Text)
    date = Column('date', DateTime)


    def __init__(self, contact, direction, message):
        self.contact = contact
        self.direction = direction
        self.message = message
        self.date = datetime.datetime.now()


    def __repr__(self):
        return f"MessageStat (id={self.id}, contact={self.contact}, direction={self.direction},\
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

