#! /usr/bin/env python

import fsphinx
import sphinxapi
    
def run(query, conf, offset=0, limit=1, max_results=1000):
    cl = fsphinx.FSphinxClient.FromConfig(conf)
    cl.SetLimits(offset, limit, max_results)
    cl.Query(query)
    
    if hasattr(cl, 'query'):
        print 'query:\n%s\n' % cl.query
    if hasattr(cl, 'hits'):
        print cl.hits
    if hasattr(cl, 'facets'):
        print cl.facets
    
def usage():
    print 'Usage:' 
    print '    python search.py query'
    print 
    print 'Description:' 
    print '    This program (CLI search) is for testing and debugging purposes only.'
    print 
    print 'Options:' 
    print '    -c, --conf              : path to config file (default is ./client_config.py)'
    print '    -o, --offset int        : (default is 0)'
    print '    -l, --limit  int        : (default is 1)'
    print '    -h, --help              : this help message'
    print
    print 'Email bugs/suggestions to Alex Ksikes (alex.ksikes@gmail.com)' 

import sys, getopt
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:o:l:h', 
            ['conf=', 'offset=', 'limit=', 'help'])
    except getopt.GetoptError:
        usage(); sys.exit(2)
    
    conf = 'client_config.py'
    offset = 0
    limit = 1
    max_results = 1000
    for o, a in opts:
        if o in ('-c', '--conf'):
            conf = a
        elif o in ('-o', '--offset'):
            offset = int(a)
        elif o in ('-l', '--limit'):
            limit = int(a)
        elif o in ('-h', '--help'):
            usage(); sys.exit()
    
    if len(args) < 1:
        usage()
    else:
        run(args[0], conf, offset, limit)
        
if __name__ == '__main__':
    main()
