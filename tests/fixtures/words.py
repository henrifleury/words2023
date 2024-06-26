import pytest
from app.store.words.accessor import word_status_d
from app.words.models import WordTimingModel, WordTiming


@pytest.fixture
def cur_game_1() -> dict():
    peer_id = 2000000001
    new_game = WordTimingModel(
        WordTiming(
            game_id=1,
            peer_id=peer_id,
            speaker_id=None,
            game_status=word_status_d["start"],
            timer=15,        # тест проходит только на пустой базе, нужно параметризовать фикстуру и вызвать с другим peer_id
        )
    )
    return dict({peer_id: new_game.to_dc()})

@pytest.fixture
def cur_gamers_1() -> dict():
    peer_id = 2000000001
    users_idxs = set([1, 2, 3])
    return dict({peer_id: users_idxs})
@pytest.fixture
def cur_game_2() -> dict():
    peer_id = 2000000200
    new_game = WordTimingModel(
        WordTiming(
            game_id=2,
            peer_id=peer_id,
            speaker_id=None,
            game_status=word_status_d["start"],
            timer=15,
        )
    )
    return dict({peer_id: new_game.to_dc()})

'''
@pytest.fixture
def cur_gamers_100() -> dict():
    peer_id = 2000000100
    users_idxs = set([101, 102, 103])
    return dict({peer_id: users_idxs})


def cur_gamers_200() -> dict():
    peer_id = 2000000200
    users_idxs = set([201, 202, 203])
    return dict({peer_id: users_idxs})
'''