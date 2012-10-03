#! /usr/bin/env python

import sys
import getopt

from fsphinx import FSphinxClient


def run(query, depth, flush, to_file, from_file, opts):
    cl = get_sphinx_client(opts)
    if flush:
        cl.cache.Flush()
    if from_file:
        cl.cache.Loads(from_file)
    else:
        preload_facets(query, depth, opts)
    if to_file:
        cl.cache.Dumps(to_file)


def get_sphinx_client(opts):
    cl = FSphinxClient.FromConfig(opts['conf'])
    # this must be the same as in th search
    cl.SetLimits(0, 10)
    # wait for no more than chosen minute
    cl.SetConnectTimeout(opts['timeout'])
    # set the expire on all keys which will be inserted
    cl.cache.expire = opts['expire']

    return cl


def preload_facets(query, depth, opts):
    # have we reached maximum depth
    if depth < 0: return
    else: depth -=1
    # create a new sphinx client each time
    cl = get_sphinx_client(opts)
    # allow full scan mode
    if cl.query_parser:
        query = cl.query_parser.Parse(query)
        query.ALLOW_EMPTY = True
    # let's compute the query
    print 'query = %s ...' % query,
    cl.Query(query)
    print '%s sec.' % cl.hits['time']
    # and also do it for each facet and recurse
    for f in cl.facets:
        for i, v in enumerate(f):
            preload_facets('%s (@%s %s)' % (query, f._sph_field, v['@term']), depth, opts)


def usage():
    print 'Usage:'
    print '    python preload_cache.py [options] start_query'
    print
    print 'Description:'
    print '    Load the cache with facets of start_query and any queries found in these facets.'
    print
    print 'Options:'
    print '    -c, --conf <sphinx_config>  : path to config file (default is ./sphinx_config.py)'
    print '    -d, --depth <int>           : maximum depth to go'
    print '    -f, --flush                 : flush the cache beforehand'
    print '    --dump <tofile>             : also dump the results to a file'
    print '    --load <fromfile>           : load the results from a dumped file'
    print '    --expire <int>              : expire flag on loaded keys in seconds (default -1 no expire)'
    print '    -h, --help                  : this help message'
    print
    print 'Email bugs/suggestions to Alex Ksikes (alex.ksikes@gmail.com)'


def main():
    try:
        _opts, args = getopt.getopt(sys.argv[1:], 'c:d:fh',
            ['conf=', 'depth=', 'flush', 'timeout=', 'dump=', 'load=',
             'expire=', 'help'])
    except getopt.GetoptError:
        usage(); sys.exit(2)

    query, depth, flush = args and args[0], 1, False
    to_file, from_file = '', ''
    opts = dict(conf='sphinx_config.py', timeout=60.0, expire=-1)
    for o, a in _opts:
        if o in ('-q', '--query'):
            query = a
        if o in ('-c', '--conf'):
            opts['conf'] = a
        elif o in ('-d', '--depth'):
            depth = int(a)
        elif o in ('-f', '--flush'):
            flush = True
        elif o in ('--timeout'):
            opts['timeout'] = float(a)
        elif o in ('--dump_file'):
            to_file = a
        elif o in ('--load_file'):
            from_file = a
        elif o in ('--expire'):
            opts['expire'] = int(a)
        elif o in ('-h', '--help'):
            usage(); sys.exit()

    if len(args) < 1:
        usage()
    else:
        run(query, depth, flush, to_file, from_file, opts)

if __name__ == '__main__':
    main()
