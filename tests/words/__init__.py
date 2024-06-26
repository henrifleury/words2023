'''
def dc2dict(dc: Optional[ ]):
    from dataclasses import dataclass, asdict

    class MessageHeader(BaseModel):
        message_id: uuid.UUID

        def dict(self):
            return {k: str(v) for k, v in asdict(self).items()}

    def dict(self):
        _dict = self.__dict__.copy()
        _dict['message_id'] = str(_dict['message_id'])
        return _dict
'''