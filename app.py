from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuSize,
    RichMenuRequest,
    RichMenuArea,
    RichMenuBounds,
    MessageAction
)
import requests
import json
import os

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")   
app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))       


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

def create_rich_menu_1():
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_blob_api = MessagingApiBlob(api_client)

        areas = [
            RichMenuArea(
                bounds=RichMenuBounds(
                    x=0,
                    y=0,
                    width=833,
                    height=843
                ),
                action=MessageAction(text='A')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(
                    x=834,
                    y=0,
                    width=833,
                    height=843
                ),
                action=MessageAction(text='B')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(
                    x=1663,
                    y=0,
                    width=834,
                    height=843
                ),
                action=MessageAction(text='C')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(
                    x=0,
                    y=843,
                    width=833,
                    height=843
                ),
                action=MessageAction(text='D')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(
                    x=834,
                    y=843,
                    width=833,
                    height=843
                ),
                action=MessageAction(text='E')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(
                    x=1662,
                    y=843,
                    width=834,
                    height=843
                ),
                action=MessageAction(text='F')
            )
        ]

        rich_menu_to_create = RichMenuRequest(
            size=RichMenuSize(
                width=2500,
                height=1686,
            ),
            selected=True,
            name="圖文選單1",
            chat_bar_text="查看更多資訊",
            areas=areas
        )

        rich_menu_id = line_bot_api.create_rich_menu(
            rich_menu_request=rich_menu_to_create
        ).rich_menu_id

        with open('./public/richmenu-a.png', 'rb') as image:
            line_bot_blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=bytearray(image.read()),
                _headers={'Content-Type': 'image/png'}
            )

        line_bot_api.set_default_rich_menu(rich_menu_id)

if __name__ == "__main__":
    app.run()