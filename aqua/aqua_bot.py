# -*- encoding: utf-8 -*-

import os
import re
import json
import time
import logging
from slackclient import SlackClient

from util import Util

logging.basicConfig(level=logging.INFO)


class AquaBot(object):
    CONFIG_FILE = 'config.json'
    DEFAULT_DELAY_SEC = 1

    KEY_BOT_NAME = 'bot-name'
    KEY_API_TOKEN = 'api-token'

    EVENT_TYPES_HANDLERS = {
        'message': 'handle_rtm_message',
    }

    COMMANDS_TYPE_CLASS = 'class_cmd'
    COMMANDS_TYPE_METHOD = 'method_cmd'

    # The sequential of handlers will effect the checking sequence
    COMMANDS_HANDLERS = {
        r'(^|.*\s+)(help)(\s+|$)': {
            'cmd_type': 'method_cmd',
            'method_cmd': 'show_usage',
            'usage': 'help\tShow usage information.'
        },
        r'(^|.*\s+)(hello|hi|greeting)(\s+|$)': {
            'cmd_type': 'class_cmd',
            'class_cmd': 'bot_cmd.greeting.Greeting',
            'usage': 'hello|hi|greeting\tGreeting :)'
        }
    }

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = self.load_config()
        self.commands_usage = self.load_commands_usage()

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

    def load_commands_usage(self):
        usage_fmt = '- {cmd_usage}'
        usage_list = ['今回のクエストの報酬わぁ、おいくら万円？\n']
        for command_handler_obj in self.COMMANDS_HANDLERS.values():
            command_usage = command_handler_obj.get('usage')
            if command_usage:
                usage_list.append(usage_fmt.format(cmd_usage=command_usage))
        return '\n'.join(usage_list)

    def show_usage(self, **kwargs):
        """
        There are (user_obj, channel_obj, users_list, words_list, origin_message, slack_client) contain in kwargs.
        """
        channel_obj = kwargs.get('channel_obj')
        if channel_obj:
            Util.send(send_message=self.commands_usage, channel_obj=channel_obj, slack_client=self.slack_client)
            return True
        else:
            return False

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
        is_tag_bot, users_list, words_list = self.parse_message_text(text=message)
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
                                                                                  msg=message))
        else:
            self.logger.info('[Channel: {c}/{cid}] From: {u}/{uid}, Msg: {msg}'.format(c=channel_name,
                                                                                       cid=channel_id,
                                                                                       u=user_name,
                                                                                       uid=user_id,
                                                                                       msg=message))

        # If Bot has been tagged, parsing commands
        if is_tag_bot:
            self.parse_commands(user_obj=user_obj,
                                channel_obj=channel_obj,
                                users_list=users_list,
                                words_list=words_list,
                                origin_message=message)
        return True

    def parse_message_text(self, text):
        """
        Parsing message text.
        :param text:
        :return: (Boolean, List, List). 1st is Bot be tagged. 2nd a list of user tag. 3rd a list of words.
        """
        bot_id_tag = '<@{bot_id}>'.format(bot_id=self.bot_id)
        users_list, words_list = Util.parse_text_to_users_and_words(text=text)
        is_tag_bot = False
        if bot_id_tag in users_list:
            is_tag_bot = True
        return is_tag_bot, users_list, words_list

    def parse_commands(self, user_obj, channel_obj, users_list, words_list, origin_message):
        """

        :param user_obj:
        :param channel_obj:
        :param users_list:
        :param words_list:
        :param origin_message:
        :return:
        """
        # getting id/name of channel/user
        user_id = user_obj.id if user_obj else ''
        user_name = user_obj.name if user_obj else ''
        channel_id = channel_obj.id if channel_obj else ''
        channel_name = channel_obj.name if channel_obj else ''

        self.logger.debug('=> parse_commands\n'
                          'User/ID: {u} / {uid}\nChannel/ID: {c} / {cid}\nMsg: {t}'.format(u=user_name,
                                                                                           uid=user_id,
                                                                                           c=channel_name,
                                                                                           cid=channel_id,
                                                                                           t=origin_message))

        # if there is text message
        # looping all commands handlers
        for loaded_command_re in self.COMMANDS_HANDLERS.keys():
            # if match then do command
            re_ret = re.match(loaded_command_re, origin_message)
            if re_ret:
                command_handler_obj = self.COMMANDS_HANDLERS.get(loaded_command_re)
                command_type = command_handler_obj.get('cmd_type')

                if command_type == self.COMMANDS_TYPE_CLASS:
                    # getting the command information
                    command_class_name = command_handler_obj.get(self.COMMANDS_TYPE_CLASS)
                    if command_class_name:
                        self.logger.info('=> parse_commands: WORD [{w}] to CMD_C [{cmd}]'.format(w=re_ret.groups(),
                                                                                                 cmd=command_class_name))
                        # getting cmd class and running
                        cmd_clz = Util.load_cmd_class(command_class_name)
                        # command interface:
                        #     user_obj, channel_obj, users_list, words_list, origin_message, slack_client
                        cmd_obj = cmd_clz(user_obj=user_obj,
                                          channel_obj=channel_obj,
                                          users_list=users_list,
                                          words_list=words_list,
                                          origin_message=origin_message,
                                          slack_client=self.slack_client)
                        return cmd_obj.run()
                elif command_type == self.COMMANDS_TYPE_METHOD:
                    # if there is no command class, check the build-in command
                    command_method_name = command_handler_obj.get(self.COMMANDS_TYPE_METHOD)
                    self.logger.info('=> parse_commands: WORD [{w}] to CMD_M [{cmd}]'.format(w=re_ret.groups(),
                                                                                             cmd=command_method_name))
                    return self.__getattribute__(command_method_name)(user_obj=user_obj,
                                                                      channel_obj=channel_obj,
                                                                      users_list=users_list,
                                                                      words_list=words_list,
                                                                      origin_message=origin_message,
                                                                      slack_client=self.slack_client)

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
