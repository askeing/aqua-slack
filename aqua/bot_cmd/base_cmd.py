# -*- encoding: utf-8 -*-
from util import Util


class BaseCmd(object):

    def __init__(self, user_obj, channel_obj, users_list, words_list, origin_message, slack_client):
        self.slack_client = slack_client
        self.user_obj = user_obj
        self.channel_obj = channel_obj
        self.users_list = users_list
        self.words_list = words_list
        self.origin_message = origin_message

    def send(self, send_message):
        Util.send(send_message=send_message, channel_obj=self.channel_obj, slack_client=self.slack_client)

    def run(self):
        raise NotImplemented('This is BaseCmd.')
