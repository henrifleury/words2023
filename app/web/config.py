import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str
    group_id: int
    vkapi_ver: str


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class WordGameConfig:
    init_time: int = 15
    quest_time: int = 15
    vote_time: int = 15


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None
    word_game: WordGameConfig = None
    mode: str = None
    config_path: str = None


def setup_config(app: "Application", config_path: str, mode: str):
    # TODO в зависимости от режима mode можно грузить разный config
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"],
            vkapi_ver=raw_config["bot"]["vkapi_ver"],
        ),
        word_game=WordGameConfig(
            init_time=raw_config["word_game"]["init_time"],
            quest_time=raw_config["word_game"]["quest_time"],
            vote_time=raw_config["word_game"]["vote_time"],
        ),
        database=DatabaseConfig(**raw_config["database"]),
        mode=mode,
        config_path=config_path,
    )
