import typing
from hashlib import sha256

import yaml
from sqlalchemy import select

from app.admin.models import Admin, AdminModel
from app.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):

    async def get_by_email(self, email: str) -> Admin | None:
        # так тоже работает async with self.app.database.session() as session:
        async with self.app.database.session.begin() as session:
            admin = await session.scalars(select(AdminModel).where(AdminModel.email == email))
            admin = admin.unique().first()
        return admin

    async def create_admin(self, email: str, password: str) -> Admin:
        new_admin = AdminModel(
            email=email,
            password=sha256(password.encode()).hexdigest(),
        )
        async with self.app.database.session.begin() as session:
            session.add(new_admin)
        return Admin(id=new_admin.id, email=new_admin.email)

    async def set_word_param(self, init_time: int = 15, quest_time: int = 15, vote_time: int = 15) -> bool:
        with open(self.app.config.config_path, "r") as f:
            raw_config = yaml.safe_load(f)
            raw_config["word_game"]["init_time"] = init_time if init_time else raw_config["word_game"]["init_time"]
            raw_config["word_game"]["quest_time"] = quest_time if quest_time else raw_config["word_game"]["quest_time"]
            raw_config["word_game"]["vote_time"] = vote_time if vote_time else raw_config["word_game"]["vote_time"]
        with open(self.app.config.config_path, "w") as f:
            yaml.safe_dump(raw_config, f)

        return raw_config["word_game"]
