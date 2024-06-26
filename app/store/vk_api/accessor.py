import random
import typing
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.bot.keyboards import keyboard_test, keyboard_empty
from app.store.bot.manager import GAME_START_KW
from app.store.vk_api.dataclasses import Message, Update, UpdateObject
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application

API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        self.logger.info("start polling")

        await self.send_message(
            Message(
                user_id=None,  # update.object.user_id,
                text=f"Всем привет, с вами игра в слова. Если хотите поиграть - отправьте в чат '{GAME_START_KW}'",
                keyboard=keyboard_empty,
                #keyboard=keyboard_test,
                peer_id=2000000002,
            )
        )


        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    # @staticmethod
    def _build_query(self, host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = self.app.config.bot.vkapi_ver  # "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="groups.getLongPollServer",
                params={
                    "group_id": self.app.config.bot.group_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = int(data["ts"])
            self.logger.info(self.server)

    async def poll(self):
        async with self.session.get(
            self._build_query(
                host=self.server,
                method="",
                params={
                    "act": "a_check",
                    "key": self.key,
                    "ts": self.ts,
                    "wait": 7,
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                print('accessor poll update in raw_updates=', update)
                if update["type"] == 'message_new':
                    updates.append(
                        Update(
                            type=update["type"],
                            object=UpdateObject(
                                id=update["object"]["message"]["id"],
                                user_id=update["object"]["message"]["from_id"],
                                body=update["object"]["message"]["text"],
                                peer_id=update["object"]["message"]["peer_id"],
                            ),
                        )
                    )
            # await self.app.store.bots_manager.handle_updates(updates)
            return updates

    async def send_message(self, message: Message) -> None:
        params = {
            "random_id": random.randint(1, 2 ** 32),
            "message": message.text,
            "access_token": self.app.config.bot.token, }
        if message.user_id:
            params["user_id"] = message.user_id
        if message.keyboard:
            params["keyboard"] = message.keyboard
        if message.peer_id:
            params["peer_id"] = message.peer_id
        else:
            params["peer_id"] = "-" + str(self.app.config.bot.group_id),

        async with self.session.get(
            self._build_query(
                API_PATH,
                "messages.send",
                params=params,
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)

"""
async def get_user_names(self, user_id: tuple[int]) -> None:
    async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="users.get",
                params={
                    "user_ids": user_id,
                },
            )
    ) as resp:
        data = await resp.json()
    raise NotImplemented



async def get_chats(self, chat_id: int):
    async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="messages.getChat",
                params={
                    "chat_id": chat_id,
                },
            )
    ) as resp:
        data = await resp.json()
"""