from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, TextMessage
import os
import requests


CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
CWA_API_KEY = os.getenv("CWA_API_KEY")

app = Flask(__name__)

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN or "")
line_handler = WebhookHandler(CHANNEL_SECRET or "")

@app.route("/", methods=["GET"])
def health():
    return "OK"

def get_banqiao_weather():
    if not CWA_API_KEY:
        return "❌ 尚未設定 CWA_API_KEY"

    url = (
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-069"
        f"?Authorization={CWA_API_KEY}"
        "&locationName=板橋區"
        "&elementName=T,Wx"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        location = data["records"]["locations"][0]["location"][0]
        elements = location["weatherElement"]

        weather = {}
        for element in elements:
            name = element["elementName"]
            value = element["time"][0]["elementValue"][0]["value"]
            weather[name] = value

        return (
            "📍 新北市板橋區 現在天氣\n"
            f"🌤 天氣：{weather.get('Wx', '未知')}\n"
            f"🌡 氣溫：{weather.get('T', '未知')}°C"
        )
    except requests.RequestException:
        return "❌ 查詢氣象資料失敗，請稍後再試"
    except (KeyError, IndexError, TypeError, ValueError):
        return "❌ 氣象資料格式異常，請稍後再試"


@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text.strip()

    if user_text.upper() == "PCD":
        reply_text = get_banqiao_weather()
    else:
        reply_text = "請輸入 PCD 取得板橋天氣"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)],
        )


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        abort(400)

    body = request.get_data(as_text=True)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


if __name__ == "__main__":
    app.run()
