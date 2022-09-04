from database import db
from tinydb import Query

def checkIfExistWallet(func: object):
    def wrapper(data: object):
        user_id = data.from_user.id
        wallet = db.get(Query().id == user_id)
        if (wallet != None):
            username = data.from_user.username
            if (wallet["username"] != username):
                db.update({"username": username}, Query().id == user_id)
            return func(data)
    return wrapper