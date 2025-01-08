import bcrypt
from datetime import datetime, timedelta
from database import get_user
from config import db

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def store_otp(username, otp):
    db.otps.insert_one({
        "username": username,
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    })

def verify_otp(username, otp):
    otp_doc = db.otps.find_one({
        "username": username,
        "otp": otp,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    if otp_doc:
        db.otps.delete_one({"_id": otp_doc["_id"]})
        return True
    return False
