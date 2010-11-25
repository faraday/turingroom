#!/usr/bin/env python
# encoding: utf-8
"""
utils.py

Created by Pradeep Gowda on 2008-04-23.
Copyright (c) 2008 Yashotech. All rights reserved.
"""

import sys
import os
import re


# This is exactly the same as Django's slugify
def slugify(value):
    """ Slugify a string, to make it URL friendly. """
    import unicodedata
    value = unicodedata.normalize('NFKD', value.replace(u'ı', 'i')).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+','-',value)
    
def _test():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    _test()

