from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    Answer,
    Question,
    Theme, ThemeModel, QuestionModel, AnswerModel,
)


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> Theme:
        new_theme = ThemeModel(title=title)
        async with self.app.database.session.begin() as session:
            session.add(new_theme)
            await session.commit()
        return new_theme.to_dc() if new_theme else None

    async def get_theme_by_title(self, title: str) -> Theme | None:
        async with self.app.database.session.begin() as session:
            theme = await session.scalars(select(ThemeModel).where(ThemeModel.title == title))
            theme = theme.unique().first()
        return theme.to_dc() if theme else None

    async def get_theme_by_id(self, id_: int) -> Theme | None:
        async with self.app.database.session.begin() as session:
            theme = await session.scalars(select(ThemeModel).where(ThemeModel.id == id_))
            theme = theme.unique().first()
        return theme.to_dc() if theme else None

    async def list_themes(self) -> list[Theme]:
        async with self.app.database.session.begin() as session:
            theme_list = await session.scalars(select(ThemeModel))
            theme_list = theme_list.all()
        return [theme.to_dc() if theme else None for theme in theme_list]


    async def create_answers(
        self, question_id: int, answers: list[Answer]
    ) -> list[Answer]:
        if (not question_id) or (len(answers)<1):
            return None
        async with self.app.database.session.begin() as session:
            #session.add_all(QuestionModel(question_id=question_id, answers=answers))
            session.add(AnswerModel(question_id=question_id, answers=answers))
            await session.commit()
        #return answers.to_dc() if answers else None
        return [answ.to_dc() if answ else None for answ in answers]


    async def create_question(
        self, title: str, theme_id: int, answers: list[Answer]
    ) -> Question:
        async with self.app.database.session.begin() as session:
            answ_mod_list = [AnswerModel(title=answ.title, is_correct=answ.is_correct) if answ else None
                    for answ in answers]
            question = QuestionModel(
                        title=title,
                        theme_id=theme_id,
                        answers=answ_mod_list)
            session.add(question)
            await session.commit()
        return question.to_dc() if question else None


    async def get_question_by_title(self, title: str) -> Question | None:
        async with self.app.database.session.begin() as session:
            #question_list = await session.select(QuestionModel.innerjoin(
                #AnswerModel, QuestionModel.id==AnswerModel.question_id))

            question = await session.scalars(select(QuestionModel).
                                             where(QuestionModel.title == title).
                                             options(joinedload(QuestionModel.answers)))
            question = question.unique().first()
        return question.to_dc() if question else None


    async def list_questions(self, theme_id: int | None = None) -> list[Question]:
        async with self.app.database.session.begin() as session:
            if theme_id:
                quest_list = await session.execute(select(QuestionModel).where(QuestionModel.theme_id == theme_id))
            else:
                quest_list = await session.execute(select(QuestionModel).options(selectinload(QuestionModel.answers)))
        return [question.to_dc() if question else None for question in quest_list.scalars().unique()]
