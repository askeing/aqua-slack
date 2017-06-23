# -*- encoding: utf-8 -*-

import logging
from base_cmd import BaseCmd

logger = logging.getLogger(__file__)


class Greeting(BaseCmd):

    @classmethod
    def run(cls, user_obj, channel_obj, words_list, slack_client):
        response_text = '<@{uid}> アクシズ教を！アクシズ教をお願いします！'.format(uid=user_obj.id)

        logger.info('=> To {u}: {msg}'.format(u=user_obj.name, msg=response_text))

        slack_client.api_call("chat.postMessage", channel=channel_obj.id, text=response_text, as_user=True)
        return True
