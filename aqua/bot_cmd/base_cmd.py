# -*- encoding: utf-8 -*-


class BaseCmd(object):

    @classmethod
    def run(cls, user_obj, channel_obj, words_list, slack_client):
        """

        :param user_obj:
        :param channel_obj:
        :param words_list:
        :param slack_client:
        :return:
        """
        raise NotImplemented('This is BaseCmd.')
