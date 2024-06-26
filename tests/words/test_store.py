from sqlalchemy.future import select

from app.store import Store
from app.words.models import WordTiming, WordPlayerModel
#from tests import peer_id
from tests.utils import check_empty_table_exists


class TestWordStore:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "timing")
        await check_empty_table_exists(cli, "word_player")
        await check_empty_table_exists(cli, "word")
        await check_empty_table_exists(cli, "vote")


    async def test_init_new_game(self, store: Store):  # cli,
        peer_id = 2000000001
        new_game = await store.word_game.init_new_game(peer_id)
        assert new_game
        assert type(new_game) is WordTiming
        assert store.bots_manager.current_games[peer_id] == new_game
        pass

    async def test_is_chat_playing(self, store: Store, cur_game_2: dict):  # cli,
        peer_id = list(cur_game_2.keys())[0]
        assert not await store.word_game.is_chat_playing(peer_id)
        store.bots_manager.current_games = cur_game_2
        assert await store.word_game.is_chat_playing(peer_id)


    async def test_init_add_player(self, store: Store, cur_gamers_1: dict):
        peer_id = list(cur_gamers_1.keys())[0]
        player_id = max(cur_gamers_1[peer_id])+100

        store.bots_manager.gamers = cur_gamers_1
        start_len_players = len(store.bots_manager.gamers[peer_id])
        await store.word_game.init_add_player(peer_id, player_id=player_id)

        assert len(store.bots_manager.gamers[peer_id]) == start_len_players+1
        assert player_id in store.bots_manager.gamers[peer_id]


    async def test_init_del_player(self, store: Store, cur_gamers_1: dict):
        peer_id = list(cur_gamers_1.keys())[0]
        player_id = list(cur_gamers_1[peer_id])[0]
        not_player_id = player_id+100

        store.bots_manager.gamers = cur_gamers_1
        start_len_players = len(store.bots_manager.gamers[peer_id])
        await store.word_game.init_del_player(peer_id, player_id=not_player_id)
        assert len(store.bots_manager.gamers[peer_id]) == start_len_players

        await store.word_game.init_del_player(peer_id, player_id=player_id)
        assert len(store.bots_manager.gamers[peer_id]) == start_len_players-1
        assert player_id not in store.bots_manager.gamers[peer_id]


    async def test_set_players(self, store: Store, db_session, cur_game_1: dict, cur_gamers_1: dict):
        peer_id = list(cur_gamers_1.keys())[0]
        store.bots_manager.current_games = cur_game_1
        store.bots_manager.gamers = cur_gamers_1

        await store.word_game.set_players(peer_id=peer_id)
        game_id = store.bots_manager.current_games[peer_id].game_id

        async with db_session.begin() as session:
            res = await session.execute(select(WordPlayerModel).where(WordPlayerModel.game_id == game_id))
            player_models = res.scalars().all()

        assert cur_gamers_1[peer_id] == set([player.id for player in player_models])

        async with db_session.begin() as session:
            active_players = await session.scalars(
                select(WordPlayerModel).where(WordPlayerModel.game_id == game_id
                                              ).where(WordPlayerModel.is_active == True))
            for player in active_players.unique():
                print(player)
            #db_players = set([player.id for player in active_players.unique()])
        #assert db_players == cur_gamers_1[peer_id]


    async def test_get_active_players(self, db_session, store: Store, cur_gamers_1: dict):
        peer_id = list(cur_gamers_1.keys())[0]
        store.bots_manager.gamers = cur_gamers_1
        assert cur_gamers_1[peer_id] == store.word_game.get_active_players(peer_id)

    async def test_pop_players(self, db_session, store: Store, cur_gamers_1: dict):
        peer_id = list(cur_gamers_1.keys())[0]
        store.bots_manager.gamers = cur_gamers_1
        assert cur_gamers_1[peer_id] == store.word_game.get_active_players(peer_id)
        # TODO запрос к БД и проверка статусов игры

    async def test_game_over(self, db_session, store: Store, cur_game_1: dict):
        peer_id = list(cur_game_1.keys())[0]
        store.bots_manager.current_games = cur_game_1

        assert type(store.bots_manager.current_games) == dict
        await store.word_game.game_over(peer_id)
        assert not store.bots_manager.current_games.pop(peer_id, None)
        assert not store.bots_manager.gamers.pop(peer_id, None)
        assert not store.bots_manager.speakers.pop(peer_id, None)
        assert not store.bots_manager.current_word.pop(peer_id, None)
        assert not store.bots_manager.votes.pop(peer_id, None)
        assert not store.bots_manager.char_enabled.pop(peer_id, None)
        # TODO запрос к БД и проверка статусов игры
