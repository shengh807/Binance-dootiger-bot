import enum
from datetime import datetime as _datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class ScoreValue(Base):
    __tablename__ = "score_value"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stratgy_id = Column(String)
    trans_gb_cd = Column(String)
    score_st_cd = Column(String)
    down_st_val = Column(Float)
    up_st_val = Column(Float)
    st_score = Column(Float)
    comment = Column(String)
    time_stamp = Column(DateTime)

    def __init__(
            self,
            stratgy_id: str,
            trans_gb_cd: str,
            score_st_cd: str,
            down_st_val: float,
            up_st_val: float,
            st_score: float,
            comment: str,
    ):
        self.stratgy_id = stratgy_id
        self.trans_gb_cd = trans_gb_cd
        self.score_st_cd = score_st_cd
        self.down_st_val = down_st_val
        self.up_st_val = up_st_val
        self.st_score = st_score
        self.comment = comment

    def info(self):
        return {
            "id": self.id,
            "stratgy_id": self.stratgy_id,
            "trans_gb_cd": self.trans_gb_cd,
            "score_st_cd": self.score_st_cd,
            "down_st_val": self.down_st_val,
            "up_st_val": self.up_st_val,
            "st_score": self.st_score,
            "comment": self.comment,
        }
