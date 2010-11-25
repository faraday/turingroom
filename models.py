#!/usr/bin/python
# -*- coding: utf-8 -*-

from google.appengine.ext import db

class Entry(db.Model):
	author = db.UserProperty()
	title = db.StringProperty(required=True)
	slug = db.StringProperty(required=True)
	markdown = db.TextProperty()
	published = db.DateTimeProperty(auto_now_add=True)
	updated = db.DateTimeProperty(auto_now=True)
	body_html = db.TextProperty()
	excerpt = db.TextProperty()
	language = db.StringProperty(required=True)
	draft = db.BooleanProperty(default=True)
	
	def url(self):
	    return '/'+self.language+'/entry/'+self.slug
