import codecs
import copy
import re
import urllib
import os

import web
from web.utils import *
database = web.database


def _unicode(s):
    if isinstance(s, unicode):
        pass
    elif isinstance(s, str):
        s = s.decode('utf-8')
    else:
        s = str(s).decode('utf-8')
    return s


def utf8(s):
    if isinstance(s, str):
        pass
    elif isinstance(s, unicode):
        s = s.encode('utf-8')
    return s


def strips(s, chars=' '):
    return re.sub('(%s){2,}' % chars, chars, s).strip()


def get_all_sub_dirs(path):
    paths = []
    d = os.path.dirname(path)
    while d not in ('', '/'):
        paths.append(d)
        d = os.path.dirname(d)
    if '.' not in paths:
        paths.append('.')
    return paths


def save_attrs(obj, attr_names):
    return dict((k, copy.deepcopy(v)) for k, v in obj.__dict__.items() if k in attr_names)


def load_attrs(obj, attrs):
    for k, v in attrs.items():
        if k in obj.__dict__:
            obj.__dict__[k] = v

unquote_plus = urllib.unquote_plus


def listify(obj):
    if not isinstance(obj, list):
        obj = [obj]
    return obj

try:
    from collections import OrderedDict
except ImportError:
    try:
        from collective.ordereddict import OrderedDict
    except ImportError:
        OrderedDict = dict


def urlquote_plus(val, safe='/'):
    if val is None: return ''
    if not isinstance(val, unicode): val = str(val)
    else: val = val.encode('utf-8')
    return urllib.quote_plus(val, safe)


def open_utf8(path):
    bom = codecs.BOM_UTF8.decode('utf8')
    f = codecs.open(path, encoding='utf8')
    l = f.readline()

    if l.startswith(bom):
        yield l.lstrip(bom)
    else:
        yield l
    for l in f:
        yield l


def iterfsep(path, idx=[], sep='\t'):
    for l in open_utf8(path):
        v = l.split(sep)
        v[-1] = v[-1].strip()
        if idx:
            v = [v[i] for i in idx]
        yield v
