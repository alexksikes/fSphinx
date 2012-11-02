First you need to [install][1] the latest version of Sphinx if you have not already done so. You would do something like this:

    svn checkout http://sphinxsearch.googlecode.com/svn/trunk/ sphinxsearch-read-only
    cd sphinxsearch-read-only
    ./configure --prefix=/usr/local/sphinx
    make
    sudo make install
    
Download and extract the latest fSphinx tarball and install the package.

    wget http://github.com/alexksikes/fSphinx/tarball/master
    tar xvzf "the tar ball"
    cd "the tar ball"
    python setup.py install

Make sure you have installed the following dependencies:

    [redis][3] which is used for facet caching.
    [web.py][4] or the database module of webpy only.
    
You're done! 

What's next? Follow the [tutorial] [2] to learn how to use fSphinx.

[1]: http://sphinxsearch.com/docs/manual-2.0.1.html#installation
[2]: https://github.com/alexksikes/fSphinx/blob/master/tutorial/TUTORIAL.md
[3]: https://github.com/andymccurdy/redis-py
[4]: http://webpy.org/install