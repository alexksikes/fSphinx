import copy
import re
import os

from web.utils import *
from web.db import database

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