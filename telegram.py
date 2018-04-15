#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json

BASE_URL = 'https://api.telegram.org/bot'
def get_chat_id(token, user_token):
    url = BASE_URL + '{token}/getUpdates'.format(token=token)
    r = requests.get(url)
    request_json =r.json()
    results = request_json['result']
    for result in reversed(results):
        command = result['message']['text']
        if 'start' in command:
            u_token = command.split(' ')[1]
            if user_token == u_token:
                return result['message']['chat']['id']


def send_message(chat_id, token, text="your server is down."):
    url = BASE_URL + '{token}/sendMessage?chat_id={chat_id}&text={text}'.format(token=token,chat_id=chat_id, text=text)
    requests.post(url)