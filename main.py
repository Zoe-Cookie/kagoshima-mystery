from io import BytesIO
import math
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.exceptions import HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    ImageMessage,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, UserSource
from PIL import Image

import strings


load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
SECRET = os.getenv("SECRET")
HOST = os.getenv("HOST")

configuration = Configuration(access_token=ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=SECRET)

app = FastAPI()


@app.post("/callback")
async def callback(
    request: Request,
    x_line_signature: str = Header(),
) -> PlainTextResponse:
    body = (await request.body()).decode("utf-8")

    try:
        handler.handle(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return PlainTextResponse(content="OK")


MAX_PREVIEW_SIZE = 1_000_000  # 1MB


@app.get("/image/{fid}")
def get_image(
    fid: str,
    is_preview: bool = Query(default=False),
) -> StreamingResponse:
    expected_fid = r"^[_0-9a-zA-Z]+$"
    if re.fullmatch(expected_fid, fid) is None:
        raise HTTPException(status_code=400, detail="Invalid fid")

    path = f"images/{fid}.jpg"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    file_size = os.path.getsize(f"images/{fid}.jpg")

    def iter_file():
        image_file = BytesIO()

        with open(path, "rb") as f:
            if not is_preview or file_size < MAX_PREVIEW_SIZE:
                image_file.write(f.read())
            else:
                image = Image.open(f)
                rate = math.sqrt(MAX_PREVIEW_SIZE / file_size)
                image.thumbnail((int(image.width * rate), int(image.height * rate)))
                image.save(image_file, format="JPEG")
            
        image_file.seek(0)
        yield from image_file

    return StreamingResponse(iter_file(), media_type="image/jpeg")


def image_to_url(fid: str, is_preview: bool = False) -> str:
    return f"https://{HOST}/image/{fid}?is_preview={is_preview}"


users_state = {}


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    with ApiClient(configuration) as api_client:
        api_instance = MessagingApi(api_client)

        if not isinstance(event.source, UserSource):
            return
        user_id = event.source.user_id
        if user_id not in users_state:
            users_state[user_id] = 0
        
        profile = api_instance.get_profile(user_id)
        user_name = profile.display_name

        if not isinstance(event.message, TextMessageContent):
            return
        message = event.message.text

        reply_token = event.reply_token

        if users_state[user_id] == 0:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(text=strings.QUESTION_1),
                        ImageMessage(
                            original_content_url=image_to_url("image_1"),
                            preview_image_url=image_to_url("image_1", is_preview=True),
                        ),
                    ],
                )
            )
            users_state[user_id] = 1
        elif users_state[user_id] == 1 and message == strings.ANSWER_1:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(text=strings.RESPONSE_1 % (user_name)),
                        TextMessage(text=strings.QUESTION_2),
                        ImageMessage(
                            original_content_url=image_to_url("image_2"),
                            preview_image_url=image_to_url("image_2", is_preview=True),
                        ),
                    ],
                )
            )
            users_state[user_id] = 2
        elif users_state[user_id] == 2 and message.isalpha() and message.lower() == strings.ANSWER_2:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(text=strings.RESPONSE_2 % (user_name)),
                        TextMessage(text=strings.QUESTION_3),
                        ImageMessage(
                            original_content_url=image_to_url("image_3"),
                            preview_image_url=image_to_url("image_3", is_preview=True),
                        ),
                    ],
                )
            )
            users_state[user_id] = 3
        elif users_state[user_id] == 3 and message == strings.ANSWER_3:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(text=strings.RESPONSE_3),
                        TextMessage(text=strings.QUESTION_4),
                        ImageMessage(
                            original_content_url=image_to_url("image_4"),
                            preview_image_url=image_to_url("image_4", is_preview=True),
                        ),
                    ],
                )
            )
            users_state[user_id] = 4
        elif users_state[user_id] == 4 and message.isalpha() and message.lower() == strings.ANSWER_4:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(text=strings.RESPONSE_4 % (user_name)),
                        TextMessage(text=strings.QUESTION_5),
                        ImageMessage(
                            original_content_url=image_to_url("image_5"),
                            preview_image_url=image_to_url("image_5", is_preview=True),
                        ),
                    ],
                )
            )
            users_state[user_id] = 5
        elif users_state[user_id] == 5 and message == strings.ANSWER_5:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(text=strings.RESPONSE_5 % (user_name)),
                        TextMessage(text=strings.ENDING),
                    ],
                )
            )
            users_state[user_id] = 0
        else:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(text="不對喔!請再想想看～"),
                    ],
                )
            )