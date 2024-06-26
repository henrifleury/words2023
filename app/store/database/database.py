from typing import Optional, TYPE_CHECKING

from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.store.database import db

if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[AsyncSession] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        db_config = self.app.config.database
        # распаковать config
        self._engine = create_async_engine(
                                            URL(
                                                drivername="postgresql+asyncpg",
                                                host=db_config.host,
                                                database=db_config.database,
                                                username=db_config.user,
                                                password=db_config.password,
                                                port=db_config.port,
                                                query={}
                                                ),
                                            echo=True, future=True)
        self.session = sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

    async def disconnect(self, *_: list, **__: dict) -> None:
        # E       AttributeError: 'sessionmaker' object has no attribute 'close'
        #if self.session:
            #await self.session.close()
        if self._engine:
            await self._engine.dispose()
        pass
