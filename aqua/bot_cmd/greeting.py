# -*- encoding: utf-8 -*-
import os
import random
import logging
from base_cmd import BaseCmd

logger = logging.getLogger(os.path.basename(__file__))


class Greeting(BaseCmd):

    GREETING_MESSAGES = [
        '女神アクアの祝福を！',
        'アクシズ教を！アクシズ教をお願いします！',
        '汝！もし私の信者ならば……お金を貸してくれると助かります！',
        'うっふふふふふ。まあ、それほどでも～、ありますけど',
        'こんにちは'
    ]

    def run(self):
        greeting_msg = random.choice(self.GREETING_MESSAGES)

        if 'こんにちは' in self.origin_message or \
            'konnichi wa' in self.origin_message.lower() or \
                'konnichiwa' in self.origin_message.lower():
            greeting_msg = 'こんにちは'

        response_text = '<@{uid}> {msg}'.format(uid=self.user_obj.id,
                                                msg=greeting_msg)
        logger.info('=> To {u}: {msg}'.format(u=self.user_obj.name, msg=response_text))

        self.send(response_text)
        return True
