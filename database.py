import bcrypt
from datetime import datetime
from config import db

def create_user(username, email, phone, password, mfa_preference):
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_doc = {
        "username": username,
        "email": email,
        "phone": phone,
        "password": hashed_pw,
        "mfa_preference": mfa_preference,
        "is_verified": False,
        "created_at": datetime.utcnow()
    }
    return db.users.insert_one(user_doc)

def get_user(username):
    return db.users.find_one({"username": username})

def verify_user(username):
    return db.users.update_one(
        {"username": username},
        {"$set": {"is_verified": True}}
    )
