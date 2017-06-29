# -*- encoding: utf-8 -*-

import os
import re
import logging

from slack_user import SlackUser
from slack_channel import SlackChannel
from channels.check_channels import CheckChannels

logger = logging.getLogger(os.path.basename(__file__))


class Util(object):

    @staticmethod
    def load_slack_users(slack_client):
        """
        https://api.slack.com/methods/users.list
        :return: a list of user objects.
        """
        result_list = []
        ret = slack_client.api_call('users.list')
        if ret.get('ok'):
            origin_list = ret.get('members')
            for obj in origin_list:
                try:
                    result_list.append(SlackUser(obj))
                except Exception as e:
                    logger.warn('Loading object failed, {obj}.\n{e}'.format(obj=obj, e=e))
        else:
            logger.warn('Loading Slack users list failed.')
        return result_list

    @staticmethod
    def load_slack_channels(slack_client):
        """
        https://api.slack.com/methods/channels.list
        :return: a list of limited channel objects.
        """
        result_list = []
        ret = slack_client.api_call('channels.list')
        if ret.get('ok'):
            origin_list = ret.get('channels')
            for obj in origin_list:
                try:
                    result_list.append(SlackChannel(obj))
                except Exception as e:
                    logger.warn('Loading object failed, {obj}.\n{e}'.format(obj=obj, e=e))
        else:
            logger.warn('Loading Slack channels list failed.')
        return result_list

    @staticmethod
    def find_by_id(obj_list, obj_id):
        """
        Finding item from list by object id.
        Ref: load_slack_users(), and load_slack_channels()
        :param obj_list:
        :param obj_id:
        :return:
        """
        result = [obj for obj in obj_list if obj.id == obj_id]
        if len(result) > 0:
            return result[0]
        else:
            return None

    @staticmethod
    def find_by_name(obj_list, name):
        """
        Finding item from list by object name.
        Ref: load_slack_users(), and load_slack_channels()
        :param obj_list:
        :param name:
        :return:
        """
        result = [obj for obj in obj_list if obj.name == name]
        if len(result) > 0:
            return result[0]
        else:
            return None

    @staticmethod
    def find_user(slack_client, search_string):
        """
        User object has following attributes:
            - name
            - tz
            - real_name
            - server
            - id
        Ref:
            https://github.com/slackapi/python-slackclient/blob/master/slackclient/_user.py
            https://github.com/slackapi/python-slackclient/blob/master/slackclient/_util.py
                SearchDict
        :param slack_client:
        :param search_string:
        :return:
        """
        return slack_client.server.users.find(search_string)

    @staticmethod
    def find_channel(slack_client, search_string):
        """
        Channel object has following attributes:
            - name
            - id
            - members
            - server
        Ref:
            https://github.com/slackapi/python-slackclient/blob/master/slackclient/_channel.py
            https://github.com/slackapi/python-slackclient/blob/master/slackclient/_util.py
                SearchList
        :param slack_client:
        :param search_string:
        :return:
        """
        return slack_client.server.channels.find(search_string)

    @staticmethod
    def parse_text_to_users_and_words(text):
        """
        Parsing the input message text,
        return the (list, list), which first is a list of all user tag id in message,
        second value is a list of every word of text message.
        :param text: input message
        :return: the (list, list), which first is a list of all user tag id in message, second value is a list of every word of text message
        """
        user_tag_pattern = r'^<@U[\w]{8}>$'
        text_items = text.split()
        users_list = [item for item in text_items if re.match(user_tag_pattern, item)]
        words_list = [item for item in text_items if not re.match(user_tag_pattern, item)]
        return users_list, words_list

    @staticmethod
    def load_cmd_class(cmd_class_name):
        """
        Loading and return the command class.
        :param cmd_class_name:
        :return: bot command class.
        """
        mod_name, clz_name = cmd_class_name.rsplit('.', 1)
        mod = __import__(mod_name, fromlist=[clz_name])
        clz = getattr(mod, clz_name)
        return clz

    @staticmethod
    def send(send_message, channel_obj, slack_client):
        """
        Sending message to Channel on Slack by slack_client.
        :param send_message:
        :param channel_obj:
        :param slack_client:
        :return:
        """
        channel_checker = CheckChannels()
        if channel_checker.is_readonly(channel_obj):
            logger.info('Skip sending message.')
            return False

        ret = slack_client.api_call("chat.postMessage", channel=channel_obj.id, text=send_message, as_user=True)
        if not ret.get('ok'):
            logger.error('Sending message failed!\n{ret}'.format(ret=ret))
            return False
        return True
