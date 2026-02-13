from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent, 
    TextMessageContent)

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuSize,
    RichMenuRequest,
    RichMenuArea,
    RichMenuBounds,
    MessageAction,
    TextMessage
)
import requests
import json
import os

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")   
CWA_API_KEY = os.environ.get("CWA_API_KEY")

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))  


@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text.strip()
    print(f"收到訊息: {user_text}")  # 除錯用
    print(f"訊息的 bytes: {user_text.encode('utf-8')}")  # 檢查編碼

    if user_text == "PCD":
        weather_text = get_banqiao_weather()

        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                reply_token=event.reply_token,
                messages=[TextMessage(text=weather_text)]
            )
def get_banqiao_weather():
    api_key = os.environ.get("CWA_API_KEY")
    if not api_key:
        return "❌ 尚未設定氣象 API Key"

    url = (
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-069"
        f"?Authorization={api_key}"
        "&locationName=板橋區"
        "&elementName=T,Wx"
    )

    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    location = data["records"]["locations"][0]["location"][0]
    elements = location["weatherElement"]

    weather = {}
    for el in elements:
        name = el["elementName"]
        value = el["time"][0]["elementValue"][0]["value"]
        weather[name] = value

    return (
        "📍 新北市板橋區 即時天氣\n"
        f"🌤 天氣：{weather.get('Wx', '未知')}\n"
        f"🌡 氣溫：{weather.get('T', '未知')}°C"
    )

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
                action=MessageAction(text='現在天氣')
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