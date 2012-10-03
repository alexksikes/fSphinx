#!/usr/bin/env python

from distutils.core import setup

long_description = '''
**fSphinx** adds an easy way to perform faceted search with Sphinx_. With fSphinx
you can compute, preload or cache facets. You can select or deselect query terms
or you can easily retrieve hits from a database.

fSphinx is used in Cloud Mining: IMDb_ , DBLP_ or MEDLINE_.

To learn more, please feel free to follow the tutorial_.

.. _Sphinx: http://sphinxsearch.com
.. _IMDb: http://imdb.cloudmining.net
.. _DBLP: http://dblp.cloudmining.net
.. _MEDLINE: http://medline.cloudmining.net
.. _tutorial: https://github.com/alexksikes/fSphinx/blob/master/tutorial/README.md
'''

setup(name='fSphinx',
    version='0.5',
    description='fSphinx easily builds faceted search systems using Sphinx.',
    author='Alex Ksikes',
    author_email='alex.ksikes@gmail.com',
    url='https://github.com/alexksikes/fSphinx',
    download_url='https://github.com/alexksikes/fSphinx/tarball/master',
    packages=['fsphinx'],
    long_description=long_description,
    license='LGPL'
)
