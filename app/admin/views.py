from hashlib import sha256

from aiohttp.web import HTTPForbidden
from aiohttp.web_exceptions import HTTPUnauthorized
from aiohttp_apispec import request_schema, response_schema, docs
from aiohttp_session import new_session

from app.admin.schemes import AdminSchema, AdminLoginResponseSchema, WordParamSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.schemes import OkResponseSchema
from app.web.utils import json_response
from config import DOC_TAG


class AdminLoginView(View):
    '''    INSERT    INTO    admins(id, email, password)
        VALUES(1, 'admin@admin.com', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918');
    '''
    @docs(tags=[DOC_TAG], summary="Admin login",
          description="Admin login")
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        data = self.request['data']
        admin = await self.request.app.store.admins.get_by_email(data["email"])
        if not admin:
            raise HTTPForbidden
        if admin.password != sha256(data["password"].encode()).hexdigest():
            raise HTTPUnauthorized
        admin = AdminLoginResponseSchema().dump(admin)

        web_session = await new_session(request=self.request)
        web_session["admin"] = admin

        return json_response(data=admin)


class AdminCurrentView(View):
    @docs(tags=[DOC_TAG], summary="Get current admin ",
          description="Current admin credentials")
    @response_schema(AdminSchema, 200)
    async def get(self):
        return AdminSchema().dump(self.request.app.config.admin)


class AdminSetWordParam(AuthRequiredMixin, View):
    @docs(tags=[DOC_TAG], summary="Set game 'word' params",
          description="Set game 'word' params")
    @request_schema(WordParamSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        # TODO возможен вариант когда 3 пустых параметра приходят, его надо бы на валидации как-то отсеять
        word_cfg = await self.request.app.store.admins.set_word_param(init_time=self.data.get('init_time', None),
                                                                      quest_time=self.data.get('quest_time', None),
                                                                      vote_time=self.data.get('vote_time', None),
                                                                      )

        return json_response({"status": "ok", "data": word_cfg})


'''
    async def get(self):
        theme_id = self.data.get("theme_id", None)
        question_list = await self.store.quizzes.list_questions(theme_id=theme_id)
        question_list = {"questions": [QuestionSchema().dump(question) for question in question_list]}
        return json_response({"status": "ok", "data": question_list})'''

'''class AdminChangeCredsView(View):
    @docs(tags=[DOCS_TAG], summary="Current admin",
          description="Change current admin credentials")

    #@response_schema(AdminSchema, 200)
    async def post(self):
        #TODO сделать смену пароля по старому паролю для id  или login
        raise NotImplemented
        #return AdminSchema().dump(self.request.app.config.admin)
#TODO высылать новый пароль сообщением на  vc по vc_id'''
