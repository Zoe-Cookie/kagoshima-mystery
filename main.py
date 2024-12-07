import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header
from fastapi.exceptions import HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration




load_dotenv()
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
SECRET = os.getenv('SECRET')

configuration = Configuration(access_token=ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=SECRET)

app = FastAPI()
@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header()) -> str:
    body = (await request.body()).decode('utf-8')

    try:
        handler.handle(body, x_line_signature)
    except InvalidSignatureError as e:
        raise HTTPException(status_code=400, detail='Invalid signature')
    
    return 'OK'
