'''from aiohttp.web_exceptions import HTTPConflict, HTTPNotFound, HTTPBadRequest
from aiohttp.web_response import json_response
from aiohttp_apispec import querystring_schema, request_schema, response_schema, docs

from app.quiz.models import Answer
from app.quiz.schemes import (
    QuestionSchema,
    ThemeIdSchema,
    ThemeSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.schemes import OkResponseSchema


class ThemeAddView(AuthRequiredMixin, View):
    @docs(tags=["hw-backend-summer-2022-3-sqlalchemy"], summary="Add theme",
          description="New theme creation")
    @request_schema(ThemeSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        title = self.data["title"]

        if await self.store.quizzes.get_theme_by_title(title):
            raise HTTPConflict

        theme = await self.store.quizzes.create_theme(title=title)

        theme = ThemeSchema().dump(theme)
        return json_response({"status": "ok", "data": theme})


class ThemeListView(AuthRequiredMixin, View):
    @docs(tags=["hw-backend-summer-2022-3-sqlalchemy"], summary="List themes",
          description="Themes list generation")
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        theme_list = await self.store.quizzes.list_themes()
        theme_list = {"themes": [ThemeSchema().dump(theme) for theme in theme_list]}
        return json_response({"status": "ok", "data": theme_list})


class QuestionAddView(AuthRequiredMixin, View):
    @docs(tags=["hw-backend-summer-2022-3-sqlalchemy"], summary="Create question",
          description="Add a new question")
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        title = self.data.get("title", None)
        theme_id = self.data.get("theme_id", None)
        answers = []
        for answ in self.data.get("answers", []):
            new_answ = Answer(title=answ["title"], is_correct=answ["is_correct"])
            answers.append(new_answ)

        if len(answers) <= 1 or sum([answ.is_correct for answ in answers]) != 1:
            raise HTTPBadRequest

        theme = await self.store.quizzes.get_theme_by_title(title)
        if not theme:
            theme = await self.store.quizzes.get_theme_by_id(theme_id)
            if not theme:
                raise HTTPNotFound

        question = await self.store.quizzes.create_question(title=title, theme_id=theme_id, answers=answers)

        question = QuestionSchema().dump(question)
        return json_response({"status": "ok", "data": question})


class QuestionListView(AuthRequiredMixin, View):
    @docs(tags=["hw-backend-summer-2022-3-sqlalchemy"], summary="Question list",
          description="Question list generation")
    @querystring_schema(ThemeIdSchema)
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        theme_id = self.data.get("theme_id", None)
        question_list = await self.store.quizzes.list_questions(theme_id=theme_id)
        question_list = {"questions": [QuestionSchema().dump(question) for question in question_list]}
        return json_response({"status": "ok", "data": question_list})
'''