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
from linebot.models import TextMessage
from linebot.models import TextSendMessage


app = Flask(__name__)
VERSION = 'v0.1.1'
CC_BOT_ENDPOINT = 'http://52.192.105.98'
DEFAULT_HEADERS = {'Content-Type': 'application/json'}

CMD_TYPE_HELP = 0
CMD_TYPE_EXECUTE_SECTION = 1
CMD_TYPE_SET_CFG = 2
CMD_TYPE_SHOW_CFG = 3
CMD_TYPE_QUERY_DB = 4
CMD_TYPE_INVALID = -1
CMD_TYPE_UNKNOWN = -2

line_bot_api = LineBotApi(os.environ['Token'], timeout=60) #Your Channel Access Token
handler = WebhookHandler(os.environ['Secret']) #Your Channel Secret

CMD_DICT = {
    'run':{
        'raw_command': None,
        'type': CMD_TYPE_EXECUTE_SECTION,
        'callback': = send_execute_section_cmd,
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
        'type': CMD_TYPE_QUERY_DB,
        'callback': send_query_cmd,
        'tokens': None
    },
    'show':{
        'raw_command': None,
        'type': CMD_TYPE_SHOW_CFG,
        'callback': send_show_cfg_cmd,
        'tokens': None
    }
}


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

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    print u'event = {0}'.format(event)
    cmd_dict = procss_cmd(event.message.text)
    if cmd_dict['type'] == CMD_TYPE_HELP:
        reply_msg(event, get_help_msg())
    else:
        if cmd_dict['callback']:
            push_msg(event, u'處理中，請稍後')
            ret = cmd_dict['callback'](cmd_dict)
            reply_msg(event, ret)
        else:
            print u'{0} does not have callback function'.format(cmd_dict)


def procss_cmd(cmd):
    print u'raw command = {0}'.format(cmd)
    # cmd_dict = {
    #     'type': CMD_TYPE_INVALID,
    #     'action': '',
    #     'raw_cmd': cmd,
    #     u'cmd_tokens': list(),
    #     'callback': None
    # }
    if not cmd or not cmd.startswith('/'):
        return None

    cmd_list = cmd.split(' ')
    action = cmd_list[0][1:]  #  ignore staring '/''

    if action in CMD_DICT.keys():
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
        line_bot_api.push_message(user_id, TextSendMessage(text=msg))
    except:
        room_id = event.source.room_id
        line_bot_api.push_message(room_id, TextSendMessage(text=msg))

def send_execute_section_cmd(cmd_dict):
    try:
        action = cmd_dict['action']
        user, section = cmd_dict['tokens']
        post_url = '{0}/{1}/{2}/{3}'.format(CC_BOT_ENDPOINT, action, user, section.upper())
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


def send_show_cfg_cmd(cmd_dict):
    return send_execute_section_cmd(cmd_dict)


def get_help_msg():
    # TODO:
    # move them to statice variable, not to generate them in run-time
    msg = u'歡迎使用鎖鍊戰記機器人，目前版本 {0}\n\n'.format(VERSION)
    msg += u'==基本操作==\n'
    msg += u'Q: 如何看狀態？\n'
    msg += u'A: /run <user> STATUS\n'
    msg += u'Q: 如何買成長卡？\n'
    msg += u'A: /set <user> buy Type=char;Count=n\n'
    msg += u'A: /run <user> buy\n\n'
    msg += u'Q: 如何買武器冶鍊卡？\n'
    msg += u'A: /set <user> buy Type=weapon;Count=n\n'
    msg += u'A: /run <user> buy\n\n'
    msg += u'Q: 如何轉活動酒場的轉蛋\n'
    msg += u'A: /run <user> gacha\n\n'
    msg += u'Q: 如何查詢資料庫\n'
    msg += u'A: /query {charainfo | questdigest}> <field> <value>\n'
    msg += u'e.q: /query charainfo name 菲娜\n'
    msg += u'e.q: /query charainfo title 狐尾\n'
    msg += u'e.q: /query questdigest name 養成\n'
    msg += u'==進階操作==\n'
    msg += u'Q: 如何設定參數?'
    msg += u'A: /set <user> <SECTION> <Key=Value;Key=Value;...>\n'
    msg += u'Q: 如何顯示目前參數?'
    msg += u'A: /show <user> ALL or <any setting name>\n\n'

    return msg
# def send_cmd(cmd):
#     app.logger.debug(u'Raw command = {0}'.format(cmd))
#     # raw command <user> <ac {section} {key=v;key=v;...}
#     # raw command /<action> <user> <key=v;key=v;...>
#     post_payload = None
#     cmd_list = cmd.split(' ')
#     # print 'Cmd list = {0}'.format(cmd_list)
#     action = cmd_list[0][1:]  #  ignore staring '/''
#     if action in ['run', 'set', 'unset', 'show_setting']:
#         try:
#             user = cmd_list[1]
#         except:
#             user = None

#         try:
#             section = cmd_list[2].upper()
#         except:
#             section = None

#         try:
#             params = cmd_list[3:]
#             param_dict = dict()
#             for itm_raw in params:
#                 itms = itm_raw.split(';')
#                 for itm in itms:
#                     key, value = itm.split('=')
#                     # print key, value
#                     param_dict[key] = value
#         except:
#             param_dict = None
#         post_url = '{0}/{1}'.format(CC_BOT_ENDPOINT, action)
#         if user:
#             post_url = post_url + '/' + user
#         if section:
#             post_url = post_url + '/' + section

#     elif action in ['query']:
#         try:
#             db, field, value = cmd_list[1:4]
#         except:
#             return '參數錯誤'
#         param_dict = None
#         post_url = u'{0}/{1}/{2}/{3}/{4}'.format(CC_BOT_ENDPOINT, action, db, field, value)
#     else:
#         print 'Unsupported command {0} yet'.format(action)

#     if param_dict:
#         post_payload = json.dumps(param_dict)
#         app.logger.info(post_payload)

#     print u'Post Url = {0}'.format(post_url)
#     print u'Post Body = {0}'.format(post_payload)
#     r = requests.post(post_url, data=post_payload, headers=DEFAULT_HEADERS)
#     return r.text

def post(url, data=None, headers=DEFAULT_HEADERS):
    r = requests.post(url, data=data, headers=DEFAULT_HEADERS)
    return r.text

import os
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ['PORT'])
