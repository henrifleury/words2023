import asyncio
import datetime
import random
import typing
from typing import Optional, Dict, Set
from logging import getLogger

from app.store.bot.keyboards import keyboard_main, keyboard_empty, keyboard_start
from app.store.vk_api.dataclasses import Message, Update
from app.store.words.accessor import word_status_d
from app.words.models import WordTiming
from app.store.bot.config import *

if typing.TYPE_CHECKING:
    from app.web.app import Application

#TODO при завершении игры нужно как-то красиво закрыть задачу с игрой

class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None  # я забыл для чего это
        self.logger = getLogger("handler")

        self.current_games: Dict[int, WordTiming] = dict()
        self.gamers: Dict[int, Set[int]] = dict()
        self.speakers: Dict[int, int] = dict()
        self.current_word: Dict[int, str] = dict()  # peer_id, word
        self.game_words: Dict[int, list] = dict()  # peer_id, word
        self.votes: Dict[int, dict] = dict()
        self.char_enabled: Dict[int, str] = dict()
        self.game_task: Dict[int, asyncio.Task] = dict()

        self.task_to_kill: list[asyncio.Task] = []

        self.user_nicks: Dict[int, str] = dict()

        self.layouts = dict()  # 'заготовка под разные раскладки, брошено
        self.check_old_games()

    async def handle_updates(self, updates: list[Update]):
        for update in updates:
            peer_id = update.object.peer_id
            txt_msg = update.object.body
            user_id = update.object.user_id
            peer_game = self.current_games.get(peer_id, None)

            if not peer_game:
                if any([txt_msg == kw for kw in GAME_START_KW]):
                    self.game_task[peer_id] = asyncio.create_task(
                                                                self.start_new_game(starter_id=user_id, peer_id=peer_id)
                                                                )
            else:
                if txt_msg == STOP_PWD:
                    # прекратить игру сразу
                    await self.close_game(peer_id=peer_id, arch_status=word_status_d["break"])
                    await self.app.store.vk_api.send_message(
                        Message(
                            user_id=None,
                            text=f"{user_id} пожелал прекратить игру {peer_id}",
                            keyboard=None,
                            peer_id=peer_id,
                        )
                    )

                elif txt_msg == EXIT_PWD:
                    if user_id != peer_game.speaker_id:
                        await self.app.store.word_game.pop_player(peer_id, user_id)
                        await self.app.store.vk_api.send_message(
                            Message(user_id=None, keyboard=None, peer_id=peer_id,
                                    text=f"{user_id} пожелал покинуть игру {peer_id}",)
                                    )
                    else:
                        await self.app.store.vk_api.send_message(
                            Message(user_id=None, keyboard=None, peer_id=peer_id,
                                    text=f"Ведущий {user_id} пожелал покинуть игру {peer_id} и покинет ее, если не "
                                         f"даст ответ в отведенное время",)
                                    )


                elif any([txt_msg == kw for kw in GAME_START_KW]):
                    await self.app.store.vk_api.send_message(
                        Message(
                            # user_id=peer_id,
                            user_id=None,  # пока в чат можно в личку
                            text=f"В чате идет игра, начать новую пока нельзя",
                            keyboard=None,
                            peer_id=peer_id,
                        )
                    )

                elif peer_game.game_status == word_status_d["start"]:
                    # НАЧАЛО ИГРЫ
                    if txt_msg == MSG_PLAY:
                        await self.app.store.word_game.init_add_player(peer_id, user_id)
                    elif txt_msg == MSG_NO_PLAY:
                        await self.app.store.word_game.init_del_player(peer_id, user_id)
                elif peer_game.game_status == word_status_d["think"]:
                    if user_id == self.speakers[peer_id]:
                        if not txt_msg in [MSG_VOTE_PRO, MSG_VOTE_CONTRA]:
                            self.current_word[peer_id] = txt_msg.strip().upper()
                        else:
                            self.logger.warning(f"{user_id} voting during thinking" + str(datetime.datetime.now()))

                elif peer_game.game_status == word_status_d["vote"]:
                    # здесь возможна ситуация, когда время истекло, но статус игры еще не поменялся
                    # а голоса продолжают учитываться, можно ее обсчитать по таймингам таблицы
                    # любой пользователь, лишь бы не голосовал за это слово ранее
                    # обычное дело в спорте, пока пропустим
                    if user_id not in self.votes[peer_id].keys(): # проверка на голосование
                        vote = None
                        if txt_msg == MSG_VOTE_PRO:
                            vote = True
                        elif txt_msg == MSG_VOTE_CONTRA:
                            vote = False
                        if not (vote is None):
                            await self.app.store.word_game.send_vote(
                                peer_id=peer_id,
                                voter_id=user_id,
                                vote=vote,
                                vote_time=datetime.datetime.now(),
                            )
            for t in self.task_to_kill.copy():
                # кажется тут какая-то очередь нужна
                self.task_to_kill.remove(t)
                t.cancel()
            print("handle_updates update=", update)

    async def start_new_game(
            self, starter_id: int, peer_id: int
    ) -> Optional[WordTiming]:
        """
        Пытаемся провести игру и если удается - возвращаем победителя
        :param starter_id: - стартующий игрок
        :param peer_id: - чат для старта
        :return:
        """
        # user_names = await self.app.store.vk_api.get_chats(self, chat_id=peer_id)
        #self.user_nicks.update(user_names)

        await self.app.store.vk_api.send_message(
            Message(
                user_id=None,
                text=f"Привет {starter_id}, предлагает поиграть",
                keyboard=keyboard_start,
                peer_id=peer_id,
            )
        )

        new_game = await self.app.store.word_game.init_new_game(peer_id)
        if new_game:
            self.gamers[peer_id] = set()
            self.char_enabled[peer_id] = GOOD_RUSSIAN_CHARS
            self.game_words[peer_id] = []

        self.logger.info("START start_round " + str(datetime.datetime.now()))
        await asyncio.sleep(self.app.config.word_game.init_time)
        self.logger.info("END start_round " + str(datetime.datetime.now()))

        player_list = self.app.store.word_game.get_active_players(peer_id)  # await
        if len(player_list) < 2:
            await self.close_game(peer_id)
            return
        else:
            winner = await self.play_game(peer_id)
            await self.close_game(peer_id, winner=winner)
            return winner

    async def close_game(
            self, peer_id: int, winner: int=None, arch_status: int = word_status_d["archive"]) -> Optional[str]:
        # надо еще как-то task завершить, если запущена
        # можно победителя в WordTiming записать, если есть
        # TODO при прерывании по стопигре победителя тоже нет и есть сообщение о недостаточном числе игрогков - убрать
        await self.app.store.vk_api.send_message(
            Message(
                user_id=None,
                text=f"Игра завершилась, {'победил ' + str(winner) if winner else ' не нашлось достаточно игроков'}.",
                peer_id=peer_id,
                keyboard=keyboard_empty,
            )
        )
        await self.app.store.word_game.game_over(peer_id, arch_status=arch_status)

    async def play_game(self, peer_id: int) -> Optional[int]:
        async def get_word(
                speaker_id: int,
                timeout: int = self.app.config.word_game.quest_time,
                delay: int = 1,
        ) -> Optional[str]:
            """
            с интервалом времени слушаем очередь и если есть слово self.current_word[peer_id]
             проверяем его на уникальность, отсутствие пробелов и последнюю букву и отправляем на голосование
            :param timeout:
            :param leader_id:
            :return: word|None
            """

            async def check_word(w: str) -> Optional[str]:
                async def bad_word_message(msg_txt):
                    # TODO если нужно это слово заносить в БД , то можно добавить в word_log c timeout=0
                    #  при этом для ключа, включающего поле word уникальность не будет гарантироваться
                    #  мне все равно тк привязался ко времени
                    await self.app.store.vk_api.send_message(
                        Message(
                            user_id=None,
                            text=msg_txt,
                            peer_id=peer_id,
                            keyboard=None,
                        )
                    )

                # TODO вынести в utils
                # здесь возможны всякие хаки типа отправка слов из kириллицы и латиницы
                # в идеале язык должен задаваться первым словом - если посл буква кириллица
                # - все след слова из кириллицы и наоборот
                # пока играю на русском языке
                # не должно содержать пробелов и посторонних символов (regex?)
                # должно оканчиваться на разрешенные буквы (для некоторых слов их может быть много?
                # для других не совпадает с последней Ь)
                w = w.strip().upper()
                if len(w) < MIN_WORD_LEN:
                    await bad_word_message(msg_txt=f"{w} - недостаточно длинное слово")
                    return
                if not w[0] in self.char_enabled[peer_id]:
                    await bad_word_message(
                        msg_txt=f"Слово {w} не начинается с нужных символов"
                    )
                    return
                w_cleared = [ch for ch in w if ch in ALL_RUSSIAN_CHARS]
                if len(w) != len(w_cleared):
                    await bad_word_message(msg_txt=f"Слово {w} содержит посторонние символы")
                    return None
                game_word_set = self.app.store.word_game.get_game_words(peer_id)
                print(game_word_set)
                if w in game_word_set:
                    await bad_word_message(msg_txt=f"Слово {w} уже предлагалось в этой игре")
                    return
                return w

            self.logger = getLogger("ждем ответ от "+str(speaker_id))
            #self.speakers[peer_id] = speaker_id
            self.current_word[peer_id] = dict()
            # char_enabled обновляется только если слов приняли self.char_enabled: Dict[int, str] = dict()

            await self.app.store.vk_api.send_message(
                Message(
                    user_id=None,
                    text=f"""Отвечает {speaker_id}, осталось \n {timeout} СЕКУНД. \n 
                    Ждем слово, длиннее {MIN_WORD_LEN} символов, начинающееся с букв(ы) {self.char_enabled[peer_id]}
                    На ответ дается {timeout} cекунд. Пожалуйста, не шумите. Спасибо.
                    Борются за победу: {active_players},
                    сыграли/играют в раунде: {round_speakers},
                    завершили выступление: {game_over_players}""",
                    keyboard=keyboard_empty,
                    peer_id=peer_id,
                )
            )

            # delay = 1
            poll_nbr = timeout // delay

            for i in range(round(poll_nbr)):
                timer = timeout - i
                await self.app.store.word_game.dec_thinking_time(
                    peer_id, speaker_id, timer
                )
                # asyncio.create_task(self.app.store.word_game.dec_thinking_time(peer_id, speaker_id, timer))
                await asyncio.sleep(delay)
                speaker_word = self.app.store.word_game.get_current_word(peer_id)
                if speaker_word:
                    w_upper = await check_word(speaker_word)
                    if w_upper:
                        await self.app.store.word_game.log_current_word(
                            peer_id,
                            speaker_id,
                            answer=w_upper,
                            time=datetime.datetime.now(),
                            timeout=self.app.config.word_game.vote_time,
                        )
                        return speaker_word
                    else:
                        # надо бы через ассессор с протоколом
                        #self.app.store.word_game.set_current_word(peer_id)
                        self.app.store.bots_manager.current_word[peer_id] = None
                if timer == WARN_TIMEOUT:
                    await self.app.store.vk_api.send_message(
                        Message(
                            user_id=None,
                            text=f"Отвечает {speaker_id}, ОСТАЛОСЬ ВСЕГО {timer}c!!!",
                            keyboard=None,
                            peer_id=peer_id,
                        )
                    )
            return None

        async def get_votes(word: str):
            """
            с интервалом времени фиксируем голоса и если все проголосовали или истек таймер
            возвращаем результат
            если никто не проголосвал пока возвращаем False
            если равное число голосов возвращаем False (для динамики)
            """

            #create_task
            await self.app.store.vk_api.send_message(
                Message(
                    user_id=None,
                    text=f"{speaker_id} предложил слово {word}. Голосуем. Первое слово дороже второго.",
                    keyboard=keyboard_main,
                    peer_id=peer_id,
                )
            )

            await self.app.store.word_game.start_voting(peer_id, speaker_id)

            self.logger.info(f"{word} wating votes")
            await asyncio.sleep(self.app.config.word_game.quest_time)
            """
            delta_t = 1
            print(round(self.app.config.word_game.quest_time/delta_t))
            for i in range(round(self.app.config.word_game.quest_time/delta_t)):
                asyncio.sleep(delta_t)
                if len(self.votes) == 3:#TODO нужно посчитать сколько в чате народу
                    break"""
            self.logger.info(f"{word} votes {self.votes[peer_id]}")
            return self.app.store.bots_manager.votes[peer_id]

        def last_sym_enabled(word_upper: str) -> str:
            res = ""
            if len(word_upper) < 2:
                res = word_upper
            else:
                if word_upper[-1] in BAD_LAST_RUSSIAN_CHARS:
                    res = last_sym_enabled(word_upper[:-1])
                else:
                    res = word_upper[-1]
            if res == "Й":
                res = "ЙИ"
            return res

        async def kick_out_player(msg_txt):
            game_over_players.add(speaker_id)
            await self.app.store.vk_api.send_message(
                Message(user_id=None, text=msg_txt, keyboard=None, peer_id=peer_id, )
            )
            await self.app.store.word_game.pop_player(peer_id, speaker_id)

        round_speakers = set()  # все игроки в раунде по разу должны получить ход, здесь храним сыгравших в этом раунде
        game_over_players = set()
        players_nicks = dict()  # TODO
        answ_timeout: int = self.app.config.word_game.quest_time

        start_word = "".join(random.sample(list(GOOD_RUSSIAN_CHARS), MIN_WORD_LEN))
        self.char_enabled[peer_id] = last_sym_enabled(start_word)
        await self.app.store.vk_api.send_message(
            Message(
                user_id=None,
                text=f"Начинаем игру, первое слово {start_word} на инопланетном языке. /"
                     f"Голосовать не нужно и голосующую клавиатуру пока не дам.",
                keyboard=keyboard_empty,
                peer_id=peer_id,
            )
        )
        speaker_id = None # на случай если цикла не будет
        await self.app.store.word_game.set_players(peer_id)
        while True:
            active_players = self.app.store.word_game.get_active_players(peer_id)
            if len(active_players) < 2:
                # есть вариант что игроки разбежались, пока то да се
                break

            round_players = active_players - round_speakers
            speaker_id = random.choice(list(round_players))
            round_speakers.add(speaker_id)
            self.logger.info(f"Игроки {peer_id}, {active_players}, {round_players}, {speaker_id}", )

            word_upper = await get_word(speaker_id, answ_timeout)
            if not word_upper:
                await kick_out_player(msg_txt=f"{speaker_id} не успел прислать годный ответ и покидает игру {peer_id}")
            else:
                votes = await get_votes(word_upper)
                total_votes = len(votes)
                pro_votes = sum(votes.values())

                if total_votes > pro_votes * 2:
                    await kick_out_player(
                        msg_txt=f"{speaker_id} прислал слово: {word_upper}."
                                f"Протокол голосования {votes}: {pro_votes} голосов за,"
                                f"{total_votes-pro_votes} голосов против, {speaker_id} покидает игру {peer_id}")
                else:
                    self.char_enabled[peer_id] = last_sym_enabled(word_upper)
                # self.votes обнуляется при старте голосования, здесь тоже можно, но тогда в тесте не проверишь
                # self.votes[peer_id]=dict()

            if len(active_players) == 2 and (speaker_id in game_over_players):
                break

            if len(round_players) < 2:
                await self.app.store.vk_api.send_message(
                    Message(
                        user_id=None,
                        text=f"Все игроки сделали ход. Начинаем новый раунд. СЛЕДИМ ЗА ПЕРЕДАЧЕЙ ХОДА",
                        keyboard=keyboard_empty,
                        peer_id=peer_id,
                    )
                )
                round_speakers = set()  # прошли круг, можно снова давать слово
                if answ_timeout > MIN_WORD_LEN:
                    answ_timeout -= 1  # с каждым новым раундом уменьшаем время на ответ до минимального

        round_players = active_players - game_over_players
        return list(round_players)[0] if round_players else speaker_id
        #  при некоторых раскладах победитель может самоликвидироваться, это можно отловить,
        #  но пока для простоты будем считать что его и нет

    def check_old_games(self):
        # TODO получить состояние игры, если есть незавершенные игры восстановить
        # если нет незавершенных
        # здесь должна быть проверка рестарта через состояние таблиц БД
        # должна быть опция не восстанавливать а сбрасывать промежуточные таблицы
        # Здесь должно быть обнуление текущих баз и всякие проверки
        # и это не асинхронная функция,
        pass
