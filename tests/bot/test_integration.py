import asyncio
import random

from app.store.bot.config import MSG_PLAY, MIN_WORD_LEN, MSG_VOTE_PRO, EXIT_PWD, RUS_KW, MSG_VOTE_CONTRA
from app.store.vk_api.dataclasses import Update, UpdateObject
from app.store.words.accessor import word_status_d

peer_id = 2000001000# + random.randint(1, 1000000)
class TestGameStart:
    async def test_new_game(self, config, store, db_session):
        global peer_id
        peer_id += 1
        print(peer_id)
        config.word_game.init_time = 1
        config.word_game.quest_time = 1
        config.word_game.vote_time = 1

        #async def peer_game():
        word_len = MIN_WORD_LEN
        # старт игры
        await store.bots_manager.handle_updates(
            updates=[Update(type="message_new",
                            object=UpdateObject(id=1, user_id=1, body=RUS_KW, peer_id=peer_id, ), )
                     ]
        )
        # self.current_games.get(peer_id, None)
        # 2 или 3 подтверждения
        await asyncio.sleep(.05)
        assert int(store.bots_manager.current_games[peer_id].peer_id) == int(peer_id)
        gamers = set([1000, 1001, 1002, 1003])
        await store.bots_manager.handle_updates(
            updates=[Update(type="message_new",
                            object=UpdateObject(id=1, user_id=player, body=MSG_PLAY, peer_id=peer_id, ), )
                     for player in gamers]
        )
        assert store.bots_manager.gamers[peer_id] == gamers
        await asyncio.sleep(
            config.word_game.init_time + config.word_game.quest_time * .5)  # active_players = await self.app.store.word_game.set_players(peer_id)
        # если здесь поставить большую задержку >init_time + quest_time то вылетит игрок по таймауту из-за отсутствия ответа
        # если здесь поставить маленькую задержку < init_time, не будет значения для first_speaker
        for i in range(10):
            await asyncio.sleep(.11)
            if store.bots_manager.speakers.get(peer_id, None):
                break
            else:
                continue

        first_speaker = store.bots_manager.speakers[peer_id]
        await store.bots_manager.handle_updates(
            updates=[Update(type="message_new",
                            object=UpdateObject(id=1,
                                                user_id=first_speaker,
                                                body=store.bots_manager.char_enabled[peer_id] * word_len,
                                                peer_id=peer_id, ), )
                     ]
        )
        word_len += 1
        await asyncio.sleep(config.word_game.quest_time * .95)
        # примерно тут пошла голосовалка votes = await get_votes(word_upper)

        for i in range(10):
            await asyncio.sleep(.11)
            if store.bots_manager.current_games[peer_id].game_status == word_status_d["vote"]:
                break
            else:
                continue

        updates = [Update(type="message_new", object=UpdateObject(id=1, user_id=player, body=MSG_VOTE_PRO, peer_id=peer_id))
                    for player in gamers]
        await store.bots_manager.handle_updates(
            updates=updates
        )
        await asyncio.sleep(config.word_game.vote_time * 1.05)  # ждем обработку результатов голосования

        for i in range(10):
            if sum(store.bots_manager.votes[peer_id].values()) == len(gamers):
                break
            else:
                await asyncio.sleep(.11)

        assert sum(store.bots_manager.votes[peer_id].values()) == len(gamers)

        await asyncio.sleep(config.word_game.quest_time * .5)
        #while store.bots_manager.current_games[peer_id].game_status != word_status_d["think"]:
            #asyncio.sleep(.3)

        second_speaker = store.bots_manager.speakers[peer_id]
        await asyncio.sleep(.01)
        assert second_speaker != first_speaker
        # пусть второй водящий пожелает покинуть игру в тот момент когда у него слово
        # а первый водящий тоже покинет игру, но только слова у него сейчас нет
        await store.bots_manager.handle_updates(
            updates=[Update(type="message_new",
                            object=UpdateObject(id=1, user_id=second_speaker, body=EXIT_PWD, peer_id=peer_id, ), ),
                     Update(type="message_new",
                            object=UpdateObject(id=1, user_id=first_speaker, body=EXIT_PWD, peer_id=peer_id, ), )
                     ]
        )
        await asyncio.sleep(.05)
        # одного выкинет по запросу, второго по таймауту, хотя непонятно почему, тк таймаут кажется не истек еще
        # по секундомеру не истек а по передачам видимо истек
        assert store.bots_manager.gamers[peer_id] == gamers - set([first_speaker, second_speaker])
        await asyncio.sleep(.05)
        third_speaker = store.bots_manager.speakers[peer_id]
        assert third_speaker != first_speaker
        assert third_speaker != second_speaker

        await store.bots_manager.handle_updates(
            updates=[Update(type="message_new",
                            object=UpdateObject(id=1,
                                                user_id=third_speaker,
                                                body=store.bots_manager.char_enabled[peer_id] * word_len,
                                                peer_id=peer_id, ), )
                     ]
        )
        word_len += 1
        await asyncio.sleep(config.word_game.quest_time * .95)
        # примерно тут пошла голосовалка votes = await get_votes(word_upper)
        await store.bots_manager.handle_updates(
            updates=[Update(type="message_new",
                            object=UpdateObject(id=1, user_id=gamer, body=MSG_VOTE_CONTRA, peer_id=peer_id, ), )
                     for gamer in gamers]
        )

        # await asyncio.sleep(.01)
        # await store.word_game.game_over(peer_id=peer_id, arch_status=word_status_d["break"])
        # await asyncio.sleep(.01)
        assert store.bots_manager.current_games.get(peer_id, None)
        await asyncio.sleep(config.word_game.quest_time + config.word_game.vote_time + .01)
        assert not store.bots_manager.current_games.get(peer_id, None)
        '''game_1 = asyncio.create_task(peer_game())
        #game_2 = asyncio.create_task(peer_game())
        await game_1
        #await game_2'''