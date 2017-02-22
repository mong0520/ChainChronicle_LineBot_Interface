from linebot import LineBotApi
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent
from linebot.models import TextMessage
from linebot.models import TextSendMessage

line_bot_api = LineBotApi('K7nWNZKVDRtp22tciKkvtVLcqM3JsvgCZaJfE080VImVuOsbaprEd9+1tGHkkcD6HfPJa4G0j4xffEtZJfxxsQAsdmkABIhWzvNLVLzMHxWC2O2ERBbKKCZNy0Ks4or+LMl4wNPD6JmBpyDTpAK9AgdB04t89/1O/w1cDnyilFU=')

profile = line_bot_api.get_profile('Ua7dccb215f40c8e7924cd8d949d54ea4')
print profile, type(profile)
print profile.display_name

line_bot_api.push_message(profile.user_id, TextSendMessage(text='Hello World!'))
