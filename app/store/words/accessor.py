import asyncio
import datetime
import typing
from typing import Optional
from sqlalchemy import select, delete, update

from app.base.base_accessor import BaseAccessor
from app.words.models import (
    WordTimingModel,
    WordTiming,
    WordPlayer,
    WordPlayerModel,
    WordLogModel,
    VoteLogModel,
)

word_status_d = {"unknown": -3, "break": -2, "archive": -1, "start": 0, "think": 1, "vote": 2}  # ,


# peer_id":2000000002


class WordsAccessor(BaseAccessor):

    async def init_new_game(self, peer_id: int) -> Optional[WordTiming]:
        new_game = WordTimingModel(
            WordTiming(
                game_id=None,
                peer_id=peer_id,
                speaker_id=None,
                game_status=word_status_d["start"],
                timer=self.app.config.word_game.init_time,
            )
        )
        """
        async with self.app.database.session.begin() as session:
            # сейчас необязательно делать запись, только если процедуру старта тоже восстанавливать
            session.add(new_game)
            await session.commit()
        """
        new_game = new_game.to_dc() if new_game else None
        self.app.store.bots_manager.current_games[peer_id] = new_game
        self.logger.info(f"init_new_game {peer_id}")
        self.app.store.bots_manager.gamers[peer_id] = set()

        return new_game

    '''
    async def is_chat_playing(self, peer_id: int) -> bool:
        """
        если в таблице WordTimingModel есть записи для peer_id - значит игра уже идет
        :param peer_id:
        :return:

        """
        """
        async with self.app.database.session.begin() as session:
            games = await session.scalars(select(WordTimingModel).where(WordTimingModel.peer_id == peer_id))
            return True if games.unique().first() else False"""
        is_chat_playing = self.app.store.bots_manager.current_games.get(peer_id, None)
        self.logger.info(f"is_chat_playing {peer_id} {is_chat_playing}")
        return True if is_chat_playing else False
    '''
    # убрать async
    async def init_add_player(self, peer_id: int, player_id: int) -> None:
        chat_gamers = self.app.store.bots_manager.gamers.get(peer_id, None)
        if type(chat_gamers) == set:
            chat_gamers |= {player_id}
            self.logger.info(f"init_add_player {peer_id} {player_id}")
        else:
            self.logger.warning(
                f"init_add_player chat_gamers {peer_id} {player_id} is not a set"
            )

    # убрать async
    async def init_del_player(self, peer_id: int, player_id: int) -> None:
        chat_gamers = self.app.store.bots_manager.gamers.get(peer_id, None)
        if type(chat_gamers) == set:
            self.app.store.bots_manager.gamers[peer_id] -= {player_id}
            self.logger.info(f"init_del_player {peer_id} {player_id}")
        else:
            self.logger.warning(
                f"init_del_player chat_gamers {peer_id} {player_id} is not a set"
            )

    async def set_players(self, peer_id: int):
        player_ids = self.app.store.bots_manager.gamers[peer_id]

        new_game = self.app.store.bots_manager.current_games[peer_id]
        new_game.game_status = word_status_d["think"]
        new_game_model = WordTimingModel(new_game)

        async with self.app.database.session.begin() as session:
            session.add(new_game_model)
            await session.commit()

        game_id = new_game_model.id
        new_game.game_id = game_id

        players = [
            WordPlayerModel(id=player_id, game_id=game_id, is_active=True)
            for player_id in player_ids
        ]
        async with self.app.database.session.begin() as session:
            session.add_all(players)
            await session.commit()
        return self.app.store.bots_manager.gamers[peer_id]

    # async def get_active_players(self, peer_id: int) -> set:
    def get_active_players(self, peer_id: int) -> set:
        # все запросы на удаление/добавление пользователей должны также обновлять словари бота
        # потому по проекту он должен быть всегда актуален и к БД нет нужды обращаться
        return self.app.store.bots_manager.gamers[peer_id]
        """
        async with self.app.database.session.begin() as session:
            active_players = await session.scalars(select(WordPlayerModel).where(WordPlayerModel.game_id == peer_id
            ).where(WordPlayerModel, is_active == True))
            return [player.to_dc() for player in active_players.unique()]"""

    async def pop_player(self, peer_id: int, player_id: int) -> None:
        #TODO нужно корректно отработать ситуацию , если покидает игрок имеющий слово - имхо запретить
        # пусть уходит не давая ответ
        # обновляем объект в памяти
        await self.init_del_player(peer_id, player_id)
        # как получится обновляем объект в БД
        game_id = self.app.store.bots_manager.current_games[peer_id].game_id
        async with self.app.database.session.begin() as session:
            query = (
                update(WordPlayerModel)
                .where(WordPlayerModel.id == player_id)
                .where(WordPlayerModel.game_id == game_id)
                .values(is_active=False)
            )
            await session.execute(query)
            await session.commit()
        self.logger.info(f"pop_player {peer_id} {player_id}")
        return

    async def game_over(self, peer_id: int, arch_status: int = word_status_d["archive"]) -> None:
        chat_game = self.app.store.bots_manager.current_games.get(peer_id, None)
        game_status = chat_game.game_status
        self.app.store.bots_manager.current_games.pop(peer_id, None)
        self.app.store.bots_manager.gamers.pop(peer_id, None)
        self.app.store.bots_manager.speakers.pop(peer_id, None)
        self.app.store.bots_manager.current_word.pop(peer_id, None)
        self.app.store.bots_manager.votes.pop(peer_id, None)
        self.app.store.bots_manager.char_enabled.pop(peer_id, None)
        self.app.store.bots_manager.game_words.pop(peer_id, None)

        game_task = self.app.store.bots_manager.game_task.pop(peer_id, None)
        if game_task:
            #game_task.cancel()
            self.app.store.bots_manager.task_to_kill.append(game_task)


        if chat_game:
            if game_status > 0:
                game_status = arch_status
                # TODO сделать одним запросом
                async with self.app.database.session.begin() as session:
                    query = (
                        update(WordTimingModel)
                        .where(WordTimingModel.peer_id == peer_id)
                        .values(game_status=game_status)
                    )
                    await session.execute(query)
                    await session.commit()

    async def dec_thinking_time(
        self, peer_id: int, speaker_id: int, timer: datetime.datetime
    ) -> None:
        game = self.app.store.bots_manager.current_games[peer_id]
        game.speaker_id = speaker_id
        game.game_status = word_status_d["think"]
        game.timer = timer

        self.app.store.bots_manager.speakers[peer_id] = game.speaker_id
        """
        self.app.store.bots_manager.current_games[peer_id].game_status = game.game_status
        """

        async def update_db():
            async with self.app.database.session.begin() as session:
                query = (
                    update(WordTimingModel)
                    .where(WordTimingModel.id == game.game_id)
                    .values(
                        speaker_id=game.speaker_id,
                        game_status=word_status_d["think"],
                        timer=timer,
                    )
                )
                await session.execute(query)
                await session.commit()
            self.logger.info(f"dec_thinking_time {game}")

        #asyncio.create_task(update_db())
        await update_db()
        return

    async def set_voting_time(self, peer_id: int,
                                    speaker_id: int,
                                    timer: datetime.datetime) -> None:
        game = self.app.store.bots_manager.current_games[peer_id]
        game.game_status = word_status_d["vote"]
        game.timer = timer


        #async def update_db():
        async def update_db():
            async with self.app.database.session.begin() as session:
                query = (
                    update(WordTimingModel)
                    .where(WordTimingModel.id == game.game_id)
                    .values(game_status=word_status_d["vote"],
                            speaker_id=speaker_id,
                            timer=timer)
                )
                await session.execute(query)
                await session.commit()
            self.logger.info(f"set_voting_time {game}")

        asyncio.create_task(update_db())
        return

    async def log_current_word(
        self, peer_id: int, player_id: int, answer: str, time: float, timeout: int
    ) -> None:
        # TODO что делать со словами за которые не проголосовали - пока остаются в логе как и в бд

        word_record = WordLogModel()
        word_record.id = self.app.store.bots_manager.current_games[peer_id].game_id
        word_record.player_id = player_id
        word_record.answer = answer
        word_record.time = time
        word_record.timeout = timeout  # self.app.config.word_game.vote_time

        async with self.app.database.session.begin() as session:
            session.add(word_record)
            await session.commit()

        self.app.store.bots_manager.game_words.setdefault(peer_id, []).append(
            word_record.to_dc()
        )
        del self.app.store.bots_manager.current_word[peer_id]

    def get_current_word(self, peer_id):  # not async
        return self.app.store.bots_manager.current_word.get(peer_id, None)

    def get_game_words(self, peer_id):  # not async
        return set(
            [w.answer for w in self.app.store.bots_manager.game_words.get(peer_id, [])]
        )

    async def start_voting(self, peer_id: int, speaker_id: int) -> None:  # not async
        self.app.store.bots_manager.current_games[peer_id].game_status = word_status_d["vote"]
        self.app.store.bots_manager.votes[peer_id] = dict()
        asyncio.create_task(self.set_voting_time(peer_id=peer_id,
                             speaker_id=speaker_id,
                             timer=self.app.config.word_game.vote_time))
        return

    async def send_vote(self, peer_id, voter_id, vote, vote_time):
        self.app.store.bots_manager.votes[peer_id][voter_id] = vote

        vote_record = VoteLogModel(
            id=self.app.store.bots_manager.current_games[peer_id].game_id,
            word_time=self.app.store.bots_manager.game_words[peer_id][-1].time,
            voter_id=voter_id,
            vote=vote,
            vote_time=vote_time,
        )

        async def update_db():
            async with self.app.database.session.begin() as session:
                session.add(vote_record)
                await session.commit()

        asyncio.create_task(update_db())
