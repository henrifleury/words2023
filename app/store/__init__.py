import typing

from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        #from app.store.quiz.accessor import QuizAccessor
        # self.quizzes = QuizAccessor(app)
        if app.config.mode == "admin":
            from app.store.admin.accessor import AdminAccessor
            self.admins = AdminAccessor(app)
        else:
            from app.store.bot.manager import BotManager
            from app.store.vk_api.accessor import VkApiAccessor
            from app.store.words.accessor import WordsAccessor

            self.vk_api = VkApiAccessor(app)
            self.word_game = WordsAccessor(app)
            self.bots_manager = BotManager(app)


def setup_store(app: "Application"):
    #if app.config.mode == "bot":
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
