import os
from datetime import datetime

import requests
import urllib3
from flask import Flask, abort, request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
CWA_API_KEY = os.getenv("CWA_API_KEY")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(CHANNEL_SECRET)


def get_banqiao_weather() -> str:
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"
    params = {
        "Authorization": CWA_API_KEY,
        "stationId": "C0AJ8",
        "format": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10, verify=False)
        response.raise_for_status()
        data = response.json()

        station = data["records"]["Station"][2]
        obs = station.get("WeatherElement", {})
        temp = obs.get("AirTemperature", "未知")
        weather = obs.get("Weather", "未知")
        humidity = obs.get("RelativeHumidity", "未知")

        daily_extreme = obs.get("DailyExtreme", {})
        high_temp = (
            daily_extreme.get("DailyHigh", {})
            .get("TemperatureInfo", {})
            .get("AirTemperature", "未知")
        )
        low_temp = (
            daily_extreme.get("DailyLow", {})
            .get("TemperatureInfo", {})
            .get("AirTemperature", "未知")
        )


        obs_time_raw = station["ObsTime"]["DateTime"]
        obs_time = datetime.fromisoformat(obs_time_raw).strftime("%Y-%m-%d %H:%M")

        return (
            "📍 新北市板橋區 當日天氣（即時觀測）\n"
            f"📡 地區：{station['StationName']}\n"
            f"🕒 觀測時間：{obs_time}\n"
            f"🌤 天氣：{weather}\n"
            f"🌡 溫度：{temp}°C\n"
            f"🔺 高溫：{high_temp}°C\n"
            f"🔻 低溫：{low_temp}°C\n"
            f"💧 濕度：{humidity}%\n"
        )
    except Exception as exc:
        app.logger.exception("Weather API error: %s", exc)
        return "❌ 查詢氣象資料失敗，請稍後再試"


@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text.strip()

    if user_text.upper() == "PCD":
        reply_text = get_banqiao_weather()
    else:
        reply_text = "請輸入 PCD 取得板橋天氣"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    if request.method == "GET":
        return "OK"

    signature = request.headers.get("X-Line-Signature")
    if not signature:
        abort(400)

    body = request.get_data(as_text=True)
    app.logger.info("Request body: %s", body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
