import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String

from .base import Base


class MessageHistory(Base):
    __tablename__ = "message_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime)
    message = Column(String)

    def __init__(self, message: String):
        self.datetime = datetime.now()
        self.message = message

    def info(self):
        return {
            "message": self.message,
        }
