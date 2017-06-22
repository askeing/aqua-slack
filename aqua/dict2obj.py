# -*- encoding: utf-8 -*-


class Dict2Obj(object):

    def __init__(self, dict_obj):
        if isinstance(dict_obj, dict):
            for key, value in dict_obj.items():
                if isinstance(value, (list, tuple)):
                    setattr(self, key, [Dict2Obj(item) if isinstance(item, dict) else item for item in value])
                else:
                    setattr(self, key, Dict2Obj(value) if isinstance(value, dict) else value)


if __name__ == '__main__':
    my_dict = {'id': 9527,
               'name': '5566 always alive.',
               'NumberOne': 'Taiwan'}
    obj = Dict2Obj(my_dict)

    print('id {}'.format(obj.id))
    print('name {}'.format(obj.name))
    print('{} Number One!'.format(obj.NumberOne))
