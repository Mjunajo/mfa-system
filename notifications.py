import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import (
    EMAIL_ADDRESS, 
    EMAIL_APP_PASSWORD, 
    twilio_client, 
    TWILIO_PHONE_NUMBER
)
import random

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_email_otp(email, otp):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = 'Your OTP for MFA System'
    
    body = f'Your OTP is: {otp}\nValid for 5 minutes.'
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_sms_otp(phone, otp):
    try:
        message = twilio_client.messages.create(
            body=f'Your MFA System OTP is: {otp}. Valid for 5 minutes.',
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        return True
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False
