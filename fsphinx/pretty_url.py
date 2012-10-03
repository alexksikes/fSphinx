"""This module is used to transform a query into a nice url and vice versa."""

__all__ = ['PrettyUrlToQuery', 'QueryToPrettyUrl']

import urlparse
import urllib
import re
import utils

PATH_PATTERN = re.compile('(\w+)=([^/]+)|([^/]+)')


def QueryToPrettyUrl(query, root='', keep_order=True, **kwargs):
    """Takes a query either as a string or a MultiFiedQuery object and returns
    a pretty url.

    Additional url query parameters could be also specified. The order of the
    query terms is returned as a url query parameter of name "ot".
    """
    if isinstance(query, basestring):
        from queries import MultiFieldQuery
        query = MultiFieldQuery(query)
    # create the path of the url
    url = {}
    for qt in query:
        f = qt.user_field
        if not f in url:
            if f == '*':
                url[f] = ''
            else:
                url[f] = '%s=' % f
        else:
            url[f] += '|'
        status = (qt.status == '-') and '*' or ''
        url[f] += '%s%s' % (status, qt.term)
    url = '%s/' % '/'.join(url[k] for k in sorted(url.keys()))
    # handle keeping the order of the queries
    order = ''
    if keep_order:
        order = [(i, qt.user_field) for i, qt in enumerate(query)]
        order = [x[0] for x in sorted(order, key=lambda x: x[1])]
        order = ''.join(map(str, order))
    if len(order) > 1:
        kwargs['ot'] = order
    # keep other parameters being passed
    url = utils.urlquote_plus(url, safe='/|*=')
    if kwargs:
        url += '?' + urllib.urlencode(kwargs, doseq=True)

    return urlparse.urljoin(root, url)


def PrettyUrlToQuery(url, root='', order=''):
    """Transforms a pretty url into a query.

    The order of the query terms is given using a url query parameter of name "ot"
    or by explicitely using the order variable.
    """
    root = root.split('/')
    url = urlparse.urlparse(url)
    path = utils.unquote_plus(url.path)
    # make the query string from url
    query = []
    for field, terms, all in PATH_PATTERN.findall(path):
        if all and all not in root:
            terms = all
            field = '*'
        if not terms:
            continue
        for term in terms.split('|'):
            if term[0] == '*':
                status = '-'
                term = term[1:]
            else:
                status = ''
            query.append('(@%s%s %s)' % (status, field, term))
    # handle the order of the query terms
    if not order:
        order = re.search('(?:\?|&|^)ot=(\d+)', url.query)
        order = order and order.group(1)
    if order:
        order = dict((q, int(i)) for q, i in zip(query, order))
        query = sorted(query, key=lambda x: order.get(x, 0))

    return ' '.join(qt for qt in query)
