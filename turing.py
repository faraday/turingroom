#!/usr/bin/python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from handlers import *

application = webapp.WSGIApplication([
	(r'/',RootHandler),
        (r'/sitemap.xml', SitemapHandler),
	(r'/(?P<lang>\w{2})/?',MainPageHandler),
	#(r'/new',NewEntryHandler),
	(r'/(?P<lang>\w{2})/index',IndexHandler),
	(r'/(?P<lang>\w{2})/feed',FeedHandler),
	(r'/(?P<lang>\w{2})/about',AboutHandler),
	(r'/(?P<lang>\w{2})/entry/(?P<slug>[^/]+)',EntryHandler),
	(r'/(?P<lang>\w{2})/index',IndexHandler),
	(r'/(?P<lang>\w{2})/new', NewEntryHandler),
	(r'/(?P<lang>\w{2})/entry/(?P<slug>[^/]+)/edit', NewEntryHandler),
        (r'/(?P<lang>\w{2})/entry/(?P<slug>[^/]+)/del', EntryDeleteHandler),
        (r'/(?P<lang>\w{2})/entry/(?P<slug>[^/]+)/publish', EntryPublishHandler),
	])
