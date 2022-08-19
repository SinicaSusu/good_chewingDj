from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from pydub import AudioSegment
import speech_recognition as sr

import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = TextSendMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)

@handler.add(MessageEvent, message=AudioMessage)  # 取得聲音時做的事情
def handle_message_Audio(event):
    #接收使用者語音訊息並存檔
    UserID = event.source.user_id
    path="./audio/"+UserID+".wav"
    audio_content = line_bot_api.get_message_content(event.message.id)
    with open(path, 'wb') as fd:
        for chunk in audio_content.iter_content():
            fd.write(chunk)        
    fd.close()
    
    #轉檔
    AudioSegment.converter = './ffmpeg/bin/ffmpeg.exe'
    sound = AudioSegment.from_file_using_temporary_files(path)
    path = os.path.splitext(path)[0]+'.wav'
    sound.export(path, format="wav")
    
    #辨識
    r = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio = r.record(source)
    text = r.recognize_google(audio,language='zh-Hant')
    
    #回傳訊息給使用者
    event.message.text=text
    handle_message(event)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)