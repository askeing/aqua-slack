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
        'うっふふふふふ。まあ、それほどでも～、ありますけど'
    ]

    def run(self):
        response_text = '<@{uid}> {msg}'.format(uid=self.user_obj.id,
                                                msg=random.choice(self.GREETING_MESSAGES))

        logger.info('=> To {u}: {msg}'.format(u=self.user_obj.name, msg=response_text))

        self.send(response_text)
        return True
