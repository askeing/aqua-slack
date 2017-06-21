from dict2obj import Dict2Obj


class SlackChannel(Dict2Obj):
    """
    A channel object contains information about a team channel.

    {
        "id": "C024BE91L",
        "name": "fun",
        "is_channel": true,
        "created": 1360782804,
        "creator": "U024BE7LH",
        "is_archived": false,
        "is_general": false,

        "members": [
            "U024BE7LH",
            ...
        ],

        "topic": {
            "value": "Fun times",
            "creator": "U024BE7LV",
            "last_set": 1369677212
        },
        "purpose": {
            "value": "This channel is for fun",
            "creator": "U024BE7LH",
            "last_set": 1360782804
        }

        "is_member": true,

        "last_read": "1401383885.000061",
        "latest": { ... }
        "unread_count": 0,
        "unread_count_display": 0
    }
    Ref:
        https://api.slack.com/types/channel
        https://api.slack.com/methods/channels.list
    """
    def __init__(self, dict_obj):
        super(SlackChannel, self).__init__(dict_obj)
