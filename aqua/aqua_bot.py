import os
import json
import time
import logging
from slackclient import SlackClient

from util import Util
from slack_user import SlackUser

logging.basicConfig()


class AquaBot(object):
    CONFIG_FILE = 'config.json'
    DEFAULT_DELAY_SEC = 1

    KEY_BOT_NAME = 'bot-name'
    KEY_API_TOKEN = 'api-token'

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = self.load_config()
        self.bot_name = self.config_file.get(self.KEY_BOT_NAME)
        self.api_token = self.config_file.get(self.KEY_API_TOKEN)

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
        print(rtm_result)


    def run(self):
        self.logger.info('### AQUA Start ###')

        # https://api.slack.com/methods/rtm.connect
        if self.slack_client.rtm_connect():
            import pdb
            pdb.set_trace()
            while True:
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
