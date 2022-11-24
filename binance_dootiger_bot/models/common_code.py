import enum
from datetime import datetime as _datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class CommonCode(Base):
    __tablename__ = "common_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_id = Column(String)
    code_name = Column(String)
    value_id = Column(String)
    value_name = Column(String)
    comment = Column(String)
    time_stamp = Column(DateTime)

    def __init__(
            self,
            code_id: str,
            code_name: str,
            value_id: str,
            value_name: str,
            comment: str
    ):
        self.code_id = code_id
        self.code_name = code_name
        self.value_id = value_id
        self.value_name = value_name
        self.comment = comment

    def info(self):
        return {
            "id": self.id,
            "code_id": self.code_id,
            "code_name": self.code_name,
            "value_id": self.value_id,
            "value_name": self.value_name,
            "comment": self.comment,
        }
