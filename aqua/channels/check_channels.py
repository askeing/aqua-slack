# -*- encoding: utf-8 -*-

import os
import json
import logging

logger = logging.getLogger(os.path.basename(__file__))


class CheckChannels(object):
    """
    checking channels setting.
    """

    def __init__(self):
        self.CHANNELS_SETTING_FILE = 'channels_setting.json'
        self.channels_setting = self.load_channels_setting()
        self.readonly_channels = self.channels_setting.get('readonly', [])

    def load_channels_setting(self):
        """
        Loading configuration from channels_setting.json.
        :return: a dict of channels_setting.
        """
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.CHANNELS_SETTING_FILE)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(e)
                return {}
        else:
            logger.warn('There is no channel setting file, {}.'.format(file_path))
            return {}

    def is_readonly(self, original_channel_obj):
        """
        Retrun True if channel setting is read-only.
        :param original_channel_obj:
        :return:
        """
        is_readonly = False
        if original_channel_obj:
            for ro_channel_name_id in self.readonly_channels:
                if original_channel_obj.id == ro_channel_name_id or original_channel_obj.name == ro_channel_name_id:
                    is_readonly = True
                    logger.info('Channel [{c}/{cid}] is Read-only.'.format(
                        c=original_channel_obj.name,
                        cid=original_channel_obj.id))
                    break
        return is_readonly
