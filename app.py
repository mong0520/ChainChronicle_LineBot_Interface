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
from linebot.models import (
    TextSendMessage, TemplateSendMessage, ButtonsTemplate,
    PostbackTemplateAction, MessageTemplateAction,
    URITemplateAction, DatetimePickerTemplateAction,
    ConfirmTemplate, CarouselTemplate, CarouselColumn,
    ImageCarouselTemplate, ImageCarouselColumn
)
import codecs
import flickr_util
import uuid


app = Flask(__name__)
VERSION = 'v0.1.1'
CC_BOT_ENDPOINT = 'http://kks.nt1.me'
DEFAULT_HEADERS = {'Content-Type': 'application/json'}
HELP_FILE_PATH = 'cmd_help.txt'
HELP_MSG = None

CMD_TYPE_HELP = 0
CMD_TYPE_EXECUTE_SECTION = 1
CMD_TYPE_SET_CFG = 2
CMD_TYPE_SHOW_CFG = 3
CMD_TYPE_QUERY_DB = 4
CMD_TYPE_UNSET_CFG = 5
CMD_TYPE_TEST = 6
CMD_TYPE_INVALID = -1
CMD_TYPE_UNKNOWN = -2

line_bot_api = LineBotApi(os.environ['Token'], timeout=60) #Your Channel Access Token
handler = WebhookHandler(os.environ['Secret']) #Your Channel Secret


def send_execute_section_cmd(cmd_dict):
    try:
        action = cmd_dict['action']
        user, section = cmd_dict['tokens']
        post_url = u'{0}/{1}/{2}/{3}'.format(CC_BOT_ENDPOINT, action, user, section.upper())
        ret = post(post_url)
        print u'{0}'.format(ret)
        return ret
    except Exception as e:
        print e
        return str(e)

def send_query_cmd(cmd_dict):
    try:
        action = cmd_dict['action']
        db, field, value = cmd_dict['tokens']
        post_url = u'{0}/{1}/{2}/{3}/{4}'.format(CC_BOT_ENDPOINT, action, db, field, value)
        ret = post(post_url)
        print u'{0}'.format(ret)
        return ret
    except Exception as e:
        print e
        return str(e)

def send_set_cfg_cmd(cmd_dict):
    try:
        action = cmd_dict['action']
        user, section = cmd_dict['tokens'][0:2]
        post_url = u'{0}/{1}/{2}/{3}'.format(CC_BOT_ENDPOINT, action, user, section.upper())
        print cmd_dict['tokens']
        params = cmd_dict['tokens'][2:]
        param_dict = dict()
        for itm_raw in params:
            itms = itm_raw.split(';')
            for itm in itms:
                key, value = itm.split('=')
                # print key, value
                param_dict[key] = value
        post_payload = json.dumps(param_dict)
        ret = post(post_url, data=post_payload)
        print u'{0}'.format(ret)
        return ret
    except Exception as e:
        print e
        return str(e)


def send_unset_cfg_cmd(cmd_dict):
    try:
        action = cmd_dict['action']
        user, section, option = cmd_dict['tokens'][0:3]
        post_url = u'{0}/{1}/{2}/{3}/{4}'.format(CC_BOT_ENDPOINT, action, user, section.upper(), option)
        print cmd_dict['tokens']
        ret = post(post_url)
        print u'{0}'.format(ret)
        return ret
    except Exception as e:
        print e
        return str(e)


def send_show_cfg_cmd(cmd_dict):
    return send_execute_section_cmd(cmd_dict)


CMD_DICT = {
    'run':{
        'raw_command': None,
        'type': CMD_TYPE_EXECUTE_SECTION,
        'callback': send_execute_section_cmd,
        'tokens': None
    },
    'help':{
        'raw_command': None,
        'type': CMD_TYPE_HELP,
        'callback': None,
        'tokens': None
    },
    'set':{
        'raw_command': None,
        'type': CMD_TYPE_SHOW_CFG,
        'callback': send_set_cfg_cmd,
        'tokens': None
    },
    'query':{
        'raw_command': None,
        'type': CMD_TYPE_QUERY_DB,
        'callback': send_query_cmd,
        'tokens': None
    },
    'show':{
        'raw_command': None,
        'type': CMD_TYPE_SHOW_CFG,
        'callback': send_show_cfg_cmd,
        'tokens': None
    },
    'unset':{
        'raw_command': None,
        'type': CMD_TYPE_UNSET_CFG,
        'callback': send_unset_cfg_cmd,
        'tokens': None
    },
    'test':{
        'raw_command': None,
        'type': CMD_TYPE_TEST,
        'callback': send_unset_cfg_cmd,
        'tokens': None
    }
}

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

@handler.add(PostbackEvent)
def handle_postback_message(event):
    print event, type(event)
    print event.postback.data, type(event.postback.data)
    cmd = json.loads(event.postback.data)
    print cmd['cmd']
    cmd_dict = procss_cmd(cmd['cmd'])
    print cmd_dict
    ret = cmd_dict['callback'](cmd_dict)
    reply_msg(event, ret)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    print MessageEvent
    print u'event = {0}'.format(event)
    print CC_BOT_ENDPOINT
    cmd_dict = procss_cmd(event.message.text)
    if not cmd_dict:
        return None

    if cmd_dict['type'] == CMD_TYPE_HELP:
        reply_msg(event, get_help_msg())
    if cmd_dict['type'] == CMD_TYPE_TEST:
        reply_msg_btn(event, None)
    else:
        if cmd_dict['callback']:
            push_msg(event, u'處理中，請稍後')
            ret = cmd_dict['callback'](cmd_dict)
            reply_msg(event, ret)
        else:
            print u'{0} does not have callback function'.format(cmd_dict)

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


def procss_cmd(cmd):
    print u'raw command = {0}'.format(cmd)
    if not cmd or not cmd.startswith('/'):
        return None

    cmd_list = cmd.split(' ')
    action = cmd_list[0][1:]  #  ignore staring '/''

    if action in CMD_DICT.keys():
        CMD_DICT[action]['action'] = action
        CMD_DICT[action]['raw_command'] = u'{0}'.format(cmd)
        CMD_DICT[action]['tokens'] = cmd_list[1:]
        print u'Processed command = {0}'.format(CMD_DICT[action])
        return CMD_DICT[action]
    else:
        return None


def reply_msg(event, msg):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)) #reply the same message from user


def push_msg(event, msg):
    # print event.source.user_id
    try:
        user_id = event.source.user_id
        print '### User id = ', user_id
        line_bot_api.push_message(user_id, TextSendMessage(text=msg))
    except:
        room_id = event.source.room_id
        line_bot_api.push_message(room_id, TextSendMessage(text=msg))


def reply_msg_btn(event, msg):
    cmd = {'cmd': '/run mong status'}
    buttons_template_message = TemplateSendMessage(
    alt_text='Buttons template',
    template=ButtonsTemplate(
        thumbnail_image_url='https://img1.apk.tw/data/attachment/common/0f/common_959_banner.jpg',
        title='鎖鍊戰記機器人',
        text='你是不是想要？',
        actions=[
            PostbackTemplateAction(
                label='看角色狀態',
                data=json.dumps(cmd)
            ),
            MessageTemplateAction(
                label='轉蛋',
                text='message text'
            ),
            URITemplateAction(
                label='選擇關卡',
                uri='http://example.com/'
            )
        ]
    )
)
    print 'token = ', event.reply_token
    line_bot_api.reply_message(event.reply_token, buttons_template_message)


def get_help_msg():
    # TODO:
    # move them to statice variable, not to generate them in run-time
    if HELP_MSG:
        return HELP_MSG
    else:
        with open(HELP_FILE_PATH, 'r') as help_fd:
            msg = help_fd.read()
    return msg


def post(url, data=None, headers=DEFAULT_HEADERS):
    r = requests.post(url, data=data, headers=DEFAULT_HEADERS)
    return r.text



import os
if __name__ == "__main__":

    # For self-hosted ssl
    # context = ('/etc/dehydrated/certs/nt1.me/fullchain.pem', '/etc/dehydrated/certs/nt1.me/privkey.pem')
    # app.run(host='0.0.0.0', port=os.environ['PORT'], ssl_context=context)

    # for hosted service
    app.run(host='0.0.0.0', port=os.environ['PORT'])

