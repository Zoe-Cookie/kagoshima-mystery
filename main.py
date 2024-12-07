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


image_cache: dict[str, bytes] = {}
MAX_PREVIEW_SIZE = 1_000_000  # 1MB


@app.get("/image/{fid}")
def get_image(
    fid: str,
    is_preview: bool = Query(default=False),
) -> StreamingResponse:
    expected_fid = r"^[_0-9a-zA-Z]+$"
    if re.fullmatch(expected_fid, fid) is None:
        raise HTTPException(status_code=400, detail="Invalid fid")

    def iter_file():
        if fid not in image_cache:
            with open(f"images/{fid}.jpg", "rb") as f:
                image_data = f.read()
            image_cache[fid] = image_data
        else:
            image_data = image_cache[fid]

        if not is_preview or len(image_data) < MAX_PREVIEW_SIZE:
            yield image_data
        else:
            image = Image.open(image_data)
            rate = MAX_PREVIEW_SIZE / len(image_data)
            image.thumbnail((int(image.width * rate), int(image.height * rate)))
            with image.fp as f:
                while buffer := f.read(4096):
                    yield buffer

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
                        TextMessage(text=strings.QUESTION_2),
                        ImageMessage(
                            original_content_url=image_to_url("image_2"),
                            preview_image_url=image_to_url("image_2", is_preview=True),
                        ),
                    ],
                )
            )
            users_state[user_id] = 2
        elif users_state[user_id] == 2 and message == strings.ANSWER_2:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
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
                        TextMessage(text=strings.QUESTION_4),
                        ImageMessage(
                            original_content_url=image_to_url("image_4"),
                            preview_image_url=image_to_url("image_4", is_preview=True),
                        ),
                    ],
                )
            )
            users_state[user_id] = 4
        elif users_state[user_id] == 4 and message == strings.ANSWER_4:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
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
                        TextMessage(text="Congrats!"),
                    ],
                )
            )
            users_state[user_id] = 0
        else:
            api_instance.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(text="Wrong answer!"),
                    ],
                )
            )