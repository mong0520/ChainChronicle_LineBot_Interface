# -*- coding: utf-8 -*-

from flask import Flask, request, abort
import os
import requests
import itertools
import sys
import json
from linebot import LineBotApi
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent
from linebot.models import PostbackEvent
from linebot.models import TextMessage
from linebot.models import ImageMessage
from linebot.models import VideoMessage
import flickr_util
import uuid


app = Flask(__name__)
line_bot_api = LineBotApi(os.environ['Token'], timeout=60) #Your Channel Access Token
handler = WebhookHandler(os.environ['Secret']) #Your Channel Secret

@app.route("/health_check", methods=['GET'])
def health_check():
    return "alive\n"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        app.logger.info(e)
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=(ImageMessage, VideoMessage))
def handle_image_message(event):
    print u'event = {0}, type = {1}'.format(event, type(event))

    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    print 'Receieve a Image file'
    file_name = '{0}.{1}'.format(str(uuid.uuid4()), ext)
    with open(file_name, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
    print 'Image file is saved: {0}'.format(file_name)
    # print os.path.exists(file_name)
    # print os.path.getsize(file_name)
    print 'Start to upload image file to My Flickr...'
    photo_url = flickr_util.upload_image(file_name, photo_set="LineBot")
    print 'Done'
    msg = u'已存檔\n{0}'.format(photo_url)
    # reply_msg(event, msg)



import os
if __name__ == "__main__":

    # For self-hosted ssl
    # context = ('/etc/dehydrated/certs/nt1.me/fullchain.pem', '/etc/dehydrated/certs/nt1.me/privkey.pem')
    # app.run(host='0.0.0.0', port=os.environ['PORT'], ssl_context=context)

    # for hosted service
    app.run(host='0.0.0.0', port=os.environ['PORT'])

