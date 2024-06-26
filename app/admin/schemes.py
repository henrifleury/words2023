from marshmallow import Schema, fields  # , ValidationError, validates_schema


class AdminSchema(Schema):
    id = fields.Int(required=False)
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class AdminLoginResponseSchema(Schema):
    id = fields.Int(required=True)
    email = fields.Email(required=True)


class WordParamSchema(Schema):
    init_time = fields.Int(required=False)
    quest_time = fields.Int(required=False)
    vote_time = fields.Int(required=False)

'''
# TODO надо бы сделать проверку что хотя бы 1 параметр не 0
    @validates_schema
    def validate_one_param(self, data):
        if not (('init_time' in data) or ('quest_time' in data) or ('vote_time' in data)):
            raise ValidationError('No data. Any config data is required')
'''