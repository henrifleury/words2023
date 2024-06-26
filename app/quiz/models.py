'''from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Theme:
    id: Optional[int]
    title: str


class ThemeModel(db):
    __tablename__ = "themes"

    id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=False, unique=True)

    def to_dc(self):
        return Theme(id=self.id, title=self.title)
        # return Theme(**self.to_dict())


@dataclass
class Answer:
    title: str
    is_correct: bool


class AnswerModel(db):
    __tablename__ = "answers"
    id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    question_id = Column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    question = relationship("QuestionModel",
                            back_populates="answers")  # lazy="selectin" lazy="joined")#, ondelete="CASCADE"

    def to_dc(self):
        return Answer(title=self.title, is_correct=self.is_correct)


@dataclass
class Question:
    id: Optional[int]
    title: str
    theme_id: int
    answers: list["Answer"]


class QuestionModel(db):
    __tablename__ = "questions"
    id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    answers = relationship("AnswerModel", back_populates="question")
    theme_id = Column(ForeignKey("themes.id", ondelete="CASCADE"), nullable=False)

    def to_dc(self):
        return Question(id=self.id,
                        title=self.title,
                        theme_id=self.theme_id,
                        answers=[answ.to_dc() if answ else None for answ in self.answers])
'''