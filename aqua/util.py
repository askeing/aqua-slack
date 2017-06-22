# -*- encoding: utf-8 -*-


class Util(object):

    @staticmethod
    def find_by_id(obj_list, obj_id):
        result = [obj for obj in obj_list if obj.id == obj_id]
        if len(result) > 0:
            return result[0]
        else:
            return None

    @staticmethod
    def find_by_name(obj_list, name):
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
    def load_cmd_class(cmd_class_name):
        mod_name, clz_name = cmd_class_name.rsplit('.', 1)
        mod = __import__(mod_name, fromlist=[clz_name])
        clz = getattr(mod, clz_name)
        return clz
