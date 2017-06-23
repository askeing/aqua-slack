# -*- encoding: utf-8 -*-

import os
import re
import json
import time
import logging
from slackclient import SlackClient

from util import Util
from slack_user import SlackUser

logging.basicConfig(level=logging.INFO)


class AquaBot(object):
    CONFIG_FILE = 'config.json'
    DEFAULT_DELAY_SEC = 1

    KEY_BOT_NAME = 'bot-name'
    KEY_API_TOKEN = 'api-token'

    EVENT_TYPES_HANDLERS = {
        'message': 'handle_rtm_message',
    }

    COMMANDS_HANDLERS = {
        r'(^|.*\s+)(hello|hi|greeting)(\s+|$)': 'bot_cmd.greeting.Greeting',
    }

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = self.load_config()
        self.bot_name = self.config_file.get(self.KEY_BOT_NAME).lower()
        self.api_token = self.config_file.get(self.KEY_API_TOKEN)
        self.bot_id = None
        # init the slack_client
        self.slack_client = SlackClient(self.api_token)

    def load_config(self):
        """
        Loading configuration from config.json.
        :return: a dict of config.
        """
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.CONFIG_FILE)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(e)
        else:
            self.logger.error('There is no config file, {}.'.format(file_path))
        raise Exception('There is no config file, {}.'.format(file_path))

    def load_slack_users(self):
        """
        https://api.slack.com/methods/users.list
        :return: a list of user objects.
        """
        result_list = []
        ret = self.slack_client.api_call('users.list')
        if ret.get('ok'):
            origin_list = ret.get('members')
            for obj in origin_list:
                try:
                    result_list.append(SlackUser(obj))
                except Exception as e:
                    self.logger.warn('Loading object failed, {obj}.\n{e}'.format(obj=obj, e=e))
        else:
            self.logger.warn('Loading Slack users list failed.')
        return result_list

    def load_slack_channels(self):
        """
        https://api.slack.com/methods/channels.list
        :return: a list of limited channel objects.
        """
        result_list = []
        ret = self.slack_client.api_call('channels.list')
        if ret.get('ok'):
            origin_list = ret.get('channels')
            for obj in origin_list:
                try:
                    result_list.append(SlackUser(obj))
                except Exception as e:
                    self.logger.warn('Loading object failed, {obj}.\n{e}'.format(obj=obj, e=e))
        else:
            self.logger.warn('Loading Slack channels list failed.')
        return result_list

    def api_send_message(self, message, channel):
        """
        Sending message to channel.
        :param message: text message
        :param channel: the channel id
        :return: True if success, False if fail
        """
        ret = self.slack_client.api_call("chat.postMessage", channel=channel, text=message)
        if not ret.get('ok'):
            self.logger.error('Sending message faile!\n{ret}'.format(ret=ret))
            return False
        return True

    def handle_rtm(self, rtm_result):
        """
        Ref: https://api.slack.com/rtm
        :param rtm_result:
        :return:
        """
        evt_type = rtm_result.get('type')
        for evt in self.EVENT_TYPES_HANDLERS.keys():
            if evt == evt_type:
                return self.__getattribute__(self.EVENT_TYPES_HANDLERS[evt])(rtm_result)
        return False

    def handle_rtm_message(self, rtm_result):
        """

        :param rtm_result:
        :return:
        """
        self.logger.info('### RTM income payload: {}'.format(rtm_result))

        # if message changed, it will have subtype
        text = None
        if rtm_result.get('subtype') == 'message_changed':
            new_msg = rtm_result.get('message')
            if new_msg:
                text = new_msg.get('text')
                # getting user and channel id
                user_id = new_msg.get('user')
            else:
                return True
        else:
            # getting message text
            text = rtm_result.get('text')
            # getting user and channel id
            user_id = rtm_result.get('user')
        channel_id = rtm_result.get('channel')

        if text:
            message = text.encode('utf-8')
        else:
            return True

        # Skip if message comes from bot it-self
        if user_id == self.bot_id:
            self.logger.debug('Message from Bot: {msg}'.format(msg=message))
            return True

        # getting channel and user name
        user_obj = Util.find_user(self.slack_client, user_id)
        channel_obj = Util.find_channel(self.slack_client, channel_id)
        user_name = user_obj.name if user_obj else ''
        channel_name = channel_obj.name if channel_obj else ''
        self.logger.debug('=> handle_rtm_message'
                          'User/ID: {u} / {uid}\nChannel/ID: {c} / {cid}\nText: {t}'.format(u=user_name,
                                                                                            uid=user_id,
                                                                                            c=channel_name,
                                                                                            cid=channel_id,
                                                                                            t=message))

        # parsing the message
        is_tag_bot, message_words_list = self.parse_text(text=message)
        """
        Checking Direct Message.
        There are two rules:
            1. Channel Name == Channel ID.
                ex: Channel name and id is D12345678.
            2. Channel Name == User ID.
                ex: Channel name is U87654321, channel id is D12345678, user id is U87654321.
        """
        if channel_name == channel_id or channel_name == user_id:
            # Direct Message is similar as tag bot
            is_tag_bot = True
            self.logger.info('[DM: {c}/{cid}] From: {u}/{uid}, Msg: {msg}'.format(c=channel_name,
                                                                                  cid=channel_id,
                                                                                  u=user_name,
                                                                                  uid=user_id,
                                                                                  msg=message_words_list))
        else:
            self.logger.info('[Channel: {c}/{cid}] From: {u}/{uid}, Msg: {msg}'.format(c=channel_name,
                                                                                       cid=channel_id,
                                                                                       u=user_name,
                                                                                       uid=user_id,
                                                                                       msg=message_words_list))

        # If Bot has been tagged, parsing commands
        if is_tag_bot:
            self.parse_commands(user_obj=user_obj, channel_obj=channel_obj, words_list=message_words_list, origin_message=message)
        return True

    def parse_text(self, text):
        """
        Parsing the input message text,
        return the (Boolean, list), which first value is True if the message contains Bot name,
        second value is a list of every word of text message.
        :param text: input message
        :return: the (Boolean, list), which first value is True if the message contains Bot name, second value is a list of every word of text message
        """
        bot_id_tag = '<@{bot_id}>'.format(bot_id=self.bot_id)
        is_tag_bot = False
        if bot_id_tag in text:
            is_tag_bot = True
        result = [item for item in text.split() if item != bot_id_tag]
        return is_tag_bot, result

    def parse_commands(self, user_obj, channel_obj, words_list, origin_message):
        """

        :param user_obj:
        :param channel_obj:
        :param words_list:
        :return:
        """
        # getting id/name of channel/user
        user_id = user_obj.id if user_obj else ''
        user_name = user_obj.name if user_obj else ''
        channel_id = channel_obj.id if channel_obj else ''
        channel_name = channel_obj.name if channel_obj else ''

        self.logger.debug('=> parse_commands\n'
                          'User/ID: {u} / {uid}\nChannel/ID: {c} / {cid}\nText: {t}'.format(u=user_name,
                                                                                            uid=user_id,
                                                                                            c=channel_name,
                                                                                            cid=channel_id,
                                                                                            t=words_list))

        # if there is text message
        # looping all commands handlers
        for loaded_command_re in self.COMMANDS_HANDLERS.keys():
            # if match then do command
            re_ret = re.match(loaded_command_re, origin_message)
            if re_ret:
                command_class_name = self.COMMANDS_HANDLERS.get(loaded_command_re)
                if command_class_name:
                    # getting cmd class and running
                    cmd_clz = Util.load_cmd_class(command_class_name)

                    # command interface:
                    #     user_obj, channel_obj, words_list, slack_client
                    self.logger.info('=> parse_commands: WORD [{w}] to CMD [{cmd}]'.format(w=re_ret.groups(),
                                                                                           cmd=command_class_name))
                    cmd_clz.run(user_obj, channel_obj, words_list, self.slack_client)
                    return True

        """
        # if there is text message
        for word in words_list:
            # looping all commands handlers
            for loaded_command_re in self.COMMANDS_HANDLERS.keys():
                # if match then do command
                if re.match(loaded_command_re, word):
                    command_class_name = self.COMMANDS_HANDLERS.get(loaded_command_re)
                    if command_class_name:
                        # getting cmd class and running
                        cmd_clz = Util.load_cmd_class(command_class_name)

                        # command interface:
                        #     user_obj, channel_obj, words_list, slack_client
                        self.logger.info('=> parse_commands: WORD [{w}] to CMD [{cmd}]'.format(w=word, cmd=command_class_name))
                        cmd_clz.run(user_obj, channel_obj, words_list, self.slack_client)
                        return True
        """
        return True

    def run(self):
        self.logger.info('### AQUA Start ###')

        # https://api.slack.com/methods/rtm.connect
        if self.slack_client.rtm_connect():
            # getting Bot id by name
            self.bot_id = Util.find_user(self.slack_client, self.bot_name).id
            self.logger.info('Name: {botname}\nID: {botid}'.format(botname=self.bot_name, botid=self.bot_id))

            while True:
                """
                first message should be: [{u'type': u'hello'}]
                """
                rtm_ret_list = self.slack_client.rtm_read()
                if rtm_ret_list:
                    for rtm_ret in rtm_ret_list:
                        self.handle_rtm(rtm_ret)
                time.sleep(self.DEFAULT_DELAY_SEC)
        else:
            raise Exception('Connection failed.')


if __name__ == "__main__":
    bot = AquaBot()
    bot.run()
