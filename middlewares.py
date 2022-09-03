from database import db
from fastapi import Request
from tinydb import Query

def checkIfExistWallet(func: object):
    def wrapper(data: object):
        if db.get(Query().id == data.from_user.id):
            return func(data)
        else:
            return
    return wrapper