# Author: Alex Ksikes (alex.ksikes@gmail.com)

import codecs

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
