import datetime
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    String,
    Boolean,
    TIMESTAMP,
    Integer,
    ForeignKeyConstraint,
)

from app.store.database.sqlalchemy_base import db


@dataclass
class WordTiming:
    """
    здесь будем сохранять текущее время и статус игр на случай падения сервиса
    """

    game_id: Optional[int]
    peer_id: int
    speaker_id: Optional[int]
    game_status: int  # [0: start, 1: игрок обдумывает ход, 2 - голосование, -1: archive]
    timer: int  # здесь таймер в секундах


class WordTimingModel(db):
    __tablename__ = "timing"

    # game_id = Column(ForeignKey("word.game_id"), primary_key=True, autoincrement=True) # nullable=False,
    id = Column(BigInteger, primary_key=True)  # , autoincrement=True # nullable=False,
    peer_id = Column(BigInteger, nullable=False)
    speaker_id = Column(
        BigInteger, nullable=True, default=None
    )  # после создания раунда но до
    game_status = Column(Integer, nullable=False)
    timer = Column(Integer, nullable=False)

    # timer = Column(TIMESTAMP(timezone=False), nullable=False)
    def __init__(self, timing: WordTiming):
        self.id = timing.game_id
        self.peer_id = timing.peer_id
        self.speaker_id = timing.speaker_id
        self.game_status = timing.game_status
        self.timer = timing.timer

    def to_dc(self):
        return WordTiming(
            game_id=self.id,
            peer_id=self.peer_id,
            speaker_id=self.speaker_id,
            game_status=self.game_status,
            timer=self.timer,
        )


@dataclass
class WordPlayer:
    """
    Здесь список активных игроков, принимавших участие в игре
    этот список не всегда всосстанавливается из логов игры,
    тк игроки могут самоудаляться
    """

    player_id: int
    game_id: int
    is_active: bool  # не в смысле спикер, а в смысле продолжает называть слова


class WordPlayerModel(db):
    __tablename__ = "word_player"

    id = Column(BigInteger, primary_key=True)
    game_id = Column(ForeignKey("timing.id"), primary_key=True)  # nullable=False,
    is_active = Column(Boolean, nullable=False, default=True)

    def to_dc(self):
        return WordPlayer(
            player_id=self.id, game_id=self.game_id, is_active=self.is_active
        )


@dataclass
class WordLog:
    """
    Здесь список слов, проверяем на уникальность и добавляем новые слова + тайминг

    """

    game_id: int
    player_id: int
    answer: str
    time: datetime.datetime
    timeout: int


class WordLogModel(db):
    __tablename__ = "word"

    # id = Column(ForeignKey("word_player.game_id"), primary_key=True)  # game_id
    id = Column(BigInteger, primary_key=True)  # game_id
    # player_id = Column(ForeignKey("word_player.id", ondelete="CASCADE"), nullable=False)  # , ondelete="CASCADE"
    player_id = Column(BigInteger, nullable=False)  # , ondelete="CASCADE"
    answer = Column(String, nullable=False)
    time = Column(TIMESTAMP(timezone=False), nullable=False, primary_key=True)
    timeout = Column(BigInteger, nullable=False)
    # "VoteLogModel", back_populates="answer")  # lazy="selectin" lazy="joined")#,

    __table_args__ = (
        ForeignKeyConstraint(
            ("id", "player_id"),
            ("word_player.game_id", "word_player.id"),
            name="game_player",
        ),
    )

    def to_dc(self):
        return WordLog(
            game_id=self.id,
            player_id=self.player_id,
            answer=self.answer,
            time=self.time,
            timeout=self.timeout,
        )


@dataclass
class VoteLog:
    """
    Здесь список голосующих за слово, сомневаюсь, нужно ли тайминг добавлять в ключ, можно просто таймаутами все посчитать
    """

    game_id: int  # word.id - game_id
    word_time: datetime.datetime
    voter_id: int  # id ГОЛОСУЮЩЕГО ИГРОКА
    vote_time: datetime.datetime
    vote: bool  # играет или выбыл


class VoteLogModel(db):
    __tablename__ = "vote"
    # id = Column(ForeignKey("word.id"), nullable=False, primary_key=True)  # , ondelete="CASCADE" # game_id
    id = Column(
        BigInteger, nullable=False, primary_key=True
    )  # , ondelete="CASCADE" # game_id
    # word_time = Column(ForeignKey("word.time"), nullable=False, primary_key=True)  # , ondelete="CASCADE"
    word_time = Column(
        TIMESTAMP(timezone=False), nullable=False, primary_key=True
    )  # , ondelete="CASCADE"
    voter_id = Column(
        BigInteger, nullable=False, primary_key=True
    )  # любой пользователь вк, без разницы и без проверки
    vote = Column(Boolean, nullable=False)  # слово или нет
    vote_time = Column(
        TIMESTAMP(timezone=False), nullable=False
    )  # время подачи голоса, в запас для восстановления игры и/или справедливости
    # answer = relationship("WordLogModel", back_populates="vote")

    __table_args__ = (
        ForeignKeyConstraint(
            ("id", "word_time"),
            ("word.id", "word.time"),
            name="game_word_time",
        ),
    )


"""        Index(
    "game_word_time",
    "id",
    "word_time",
    unique=True,
),
"""

"""
    id = Column(BigInteger, primary_key=True)  # game_id
    #player_id = Column(ForeignKey("word_player.id", ondelete="CASCADE"), nullable=False)  # , ondelete="CASCADE"
    player_id = Column(BigInteger, nullable=False)  # , ondelete="CASCADE"
    word = Column(String, nullable=False)
    time = Column(TIMESTAMP(timezone=False), nullable=False, primary_key=True)
    timeout = Column(BigInteger, nullable=False
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ("id", "player_id"),
            ("word_player.game_id", "word_player.id"),
            name="game_player",
        ),
    )
"""

'''
# пока решил брать из контакта имена, если будет возможность задавать ники может понадобится эта модель
@dataclass
class User:
    """
    Здесь список игроков, когда-либо принимавших участие с никами
    собственно ники
    """

    vk_id: int
    nick: Optional[str]


class UserModel(db):
    __tablename__ = "user"

    vk_id = Column(BigInteger, primary_key=True)
    # если nick не задан - дублировать в nick vk_id
    # если дублировать в nick vk_id его длина может стать больше 13, но это вряд ли
    nick = Column(String(13), nullable=False, unique=True)

    def to_dc(self):
        return User(id=self.vk_id, nick=self.nick)
'''
