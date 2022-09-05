from database import db
from tinydb import Query

def checkIfExistWallet(func: object):
    def wrapper(data: object):
        user_id = data.from_user.id
        wallet = db.get(Query().id == user_id)
        if (wallet == None):
            return 
        
        if (wallet.get("admin_key") == None) and (wallet.get("invoice_key") == None):
            return None
        
        username = data.from_user.username
        if (wallet.get("username") == None):
            wallet["username"] = None
            
        if (wallet["username"] != username):
            db.update({"username": username}, Query().id == user_id)
        return func(data)
    return wrapper