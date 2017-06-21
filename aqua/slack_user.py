from dict2obj import Dict2Obj


class SlackUser(Dict2Obj):
    """
    A user object contains information about a team member.

    {
        "id": "U023BECGF",
        "name": "bobby",
        "deleted": false,
        "color": "9f69e7",
        "profile": {
            "avatar_hash": "ge3b51ca72de",
            "status_emoji": ":mountain_railway:",
            "status_text": "riding a train",
            "first_name": "Bobby",
            "last_name": "Tables",
            "real_name": "Bobby Tables",
            "email": "bobby@slack.com",
            "skype": "my-skype-name",
            "phone": "+1 (123) 456 7890",
            "image_24": "https:\/\/...",
            "image_32": "https:\/\/...",
            "image_48": "https:\/\/...",
            "image_72": "https:\/\/...",
            "image_192": "https:\/\/...",
            "image_512": "https:\/\/..."
        },
        "is_admin": true,
        "is_owner": true,
        "is_primary_owner": true,
        "is_restricted": false,
        "is_ultra_restricted": false,
        "updated": 1490054400,
        "has_2fa": false,
        "two_factor_type": "sms"
    }
    Ref:
        https://api.slack.com/types/user
        https://api.slack.com/methods/users.list
    """
    def __init__(self, dict_obj):
        super(SlackUser, self).__init__(dict_obj)
