#! /usr/bin/env python

from fsphinx import FSphinxClient
from fsphinx import MultiFieldQuery

def get_facets_from_config(conf):
    return FSphinxClient.FromConfig(conf).facets

def get_query_parser(conf):
    cl = FSphinxClient.FromConfig(conf)
    if hasattr(cl, 'query_parser'):
        q = cl.query_parser
    else:
        q = MultiFieldQuery()
    MultiFieldQuery.ALLOW_EMPTY = True
    return q

# this could be made recursive
def preload_facets(squery, conf):
    facets = get_facets_from_config(conf)
    query = get_query_parser(conf)
    
    query.Parse(squery)
    facets.Preload(query)
    print 'TOP FACET: %s in %s sec.' % (query.uniq, facets.time) 
    
    for f in facets:
        for i, v in enumerate(f):
            facets = get_facets_from_config(conf)
            
            query.Parse('%s (@%s %s)' % (squery, f._sph_field, v['@term']))
            facets.Preload(query)
            print 'FACETS %s %s/%s: %s - %s in %s sec.' % (f.name, i+1, f._max_num_values, 
                query.uniq, v['@count'], facets.time)
                
def usage():
    print 'Usage:' 
    print '    python preload.py start_query'
    print 
    print 'Description:' 
    print '    Load the cache with facets of start_query and any queries found in these facets.'
    print 
    print 'Options:' 
    print '    -c, --conf              : path to config file (default is ./sphinx_config.py)'
    print '    -h, --help              : this help message'
    print
    print 'Email bugs/suggestions to Alex Ksikes (alex.ksikes@gmail.com)' 

import sys, getopt
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:h', ['conf=', 'help'])
    except getopt.GetoptError:
        usage(); sys.exit(2)
    
    conf = 'client_config.py'
    for o, a in opts:
        if o in ('-c', '--conf'):
            conf = a
        elif o in ('-h', '--help'):
            usage(); sys.exit()
    
    if len(args) < 1:
        usage()
    else:
        preload_facets(args[0], conf)
        
if __name__ == '__main__':
    main()
