from collections.abc import Iterable
import json


class Serializable:
    pass


def serialize(instance, attrs):
    result = {}
    for k, v in attrs.items():
        result[k] = _serialize(v)
    return result


def _serialize(v):
    for type_, method in SERIALIZE_METHOD_MAP:
        if isinstance(v, type_):
            return method(v)
    return v


def deserialize(cls, values):
    kwargs = {}
    for k, v in values.items():
        kwargs[k] = _deserialize(v)
    return cls(**kwargs)


def _deserialize(v):
    for type_, method in DESERIALIZE_METHOD_MAP:
        if isinstance(v, type_):
            return method(v)
    return v


SERIALIZE_METHOD_MAP = []


def serialize_method(type_):
    def wrapper(func):
        SERIALIZE_METHOD_MAP.append((type_, func))
        return func
    return wrapper


@serialize_method(Serializable)
def serialize_serializable_type(v):
    return v.serialize()


@serialize_method(Iterable)
def serialize_iterable_type(v):
    if isinstance(v, str):
        return v
    return tuple(_serialize(i) for i in v)


@serialize_method(set)
def set_type(v):
    return serialize_iterable_type(tuple(v))


DESERIALIZE_METHOD_MAP = []


def deserialize_method(type_):
    def wrapper(func):
        DESERIALIZE_METHOD_MAP.append((type_, func))
        return func
    return wrapper


@deserialize_method(dict)
def deserilize_dict_type(v):
    return {k: _deserialize(v_) for k, v_ in v.items()}


@deserialize_method(Iterable)
def deserialize_iterable_type(v):
    if isinstance(v, str):
        return v
    return tuple(_deserialize(i) for i in v)


def serializable_class_factory(class_name, cls, target_attrs=None):
    if target_attrs and not isinstance(target_attrs, tuple):
        raise TypeError(f'target_attrs must be tuple, not {type(target_attrs)}')

    def m_serialize(self):
        if target_attrs is None:
            attrs = vars(self)
        else:
            attrs = {k: v
                     for k, v in vars(self).items()
                     if k in target_attrs}
        return serialize(self, attrs)

    @classmethod
    def m_deserialize(cls, values):
        return deserialize(cls, values)

    methods = {'serialize': m_serialize, 'deserialize': m_deserialize}
    return type(class_name, (cls, Serializable, object), methods)


def dictionarizable_class_factory(class_name, cls, target_attrs=None):
    new_class = serializable_class_factory(class_name, cls, target_attrs)

    def m_to_dict(self):
        return dict.dump(self.serialize())

    @classmethod
    def m_from_dict(cls, values):
        return cls.deserialize(values)

    new_class.to_dict = m_to_dict
    new_class.from_dict = m_from_dict
    return new_class


def jsonizeable_class_factory(class_name, cls, target_attrs=None):
    new_class = serializable_class_factory(class_name, cls, target_attrs)

    def m_to_json(self, fp):
        return json.dump(self.serialize(), fp)

    @classmethod
    def m_from_json(cls, fp):
        return cls.deserialize(json.load(fp))

    def m_to_jsons(self):
        return json.dumps(self.serialize())

    @classmethod
    def m_from_jsons(cls, s):
        return cls.deserialize(json.loads(s))

    new_class.to_json = m_to_json
    new_class.from_json = m_from_json
    new_class.to_jsons = m_to_jsons
    new_class.from_jsons = m_from_jsons
    return new_class


def dictionarizable(target_attrs=None):
    def _dictionarizable(cls):
        return dictionarizable_class_factory(cls.__name__, cls, target_attrs)
    return _dictionarizable


def jsonizable(target_attrs=None):
    def _jsonizable(cls):
        return jsonizeable_class_factory(cls.__name__, cls, target_attrs)
    return _jsonizable


@jsonizable(('a', 'b', 'c', 'd'))
class A:

    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d


@dictionarizable(('b', ))
class B:
    def __init__(self, b):
        self.b = b


a = A(1, B('1'), [3,4,5], {1,2})
assert isinstance(a, Serializable) is True
s = a.to_jsons()
print(s)
a2 = A.from_jsons(s)
print(vars(a2))
