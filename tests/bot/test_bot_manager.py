import asyncio

from app.store.vk_api.dataclasses import Message, Update, UpdateObject


peer_id = 2000001000

class TestHandleUpdates:
    async def test_no_messages(self, store):
        await store.bots_manager.handle_updates(updates=[])
        assert store.vk_api.send_message.called is False

    async def test_new_message(self, store):
        await store.bots_manager.handle_updates(
            updates=[
                Update(
                    type="message_new",
                    object=UpdateObject(
                        id=1,
                        user_id=1,
                        body="поиграем123",
                        peer_id=peer_id,
                    ),
                )
            ]
        )
        await asyncio.sleep(1)
        assert store.vk_api.send_message.call_count == 1
        message: Message = store.vk_api.send_message.mock_calls[0].args[0]
        assert message.user_id is None
        assert message.peer_id == peer_id
        assert message.text
