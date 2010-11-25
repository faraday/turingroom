#!/usr/bin/python
# -*- coding: utf-8 -*-

#from django.core.paginator import ObjectPaginator, InvalidPage
from google.appengine.ext import webapp
from google.appengine.ext import db
#from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
import os
from models import *

from lib import utils, markdown2, BeautifulSoup, textile
import functools

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import datetime

__jinja_template_loader = FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates')])
env = Environment(loader = __jinja_template_loader)

def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
        return value.strftime(format)

env.filters['datetimeformat'] = datetimeformat

def administrator(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            if self.request.method == "GET":
                self.redirect(users.create_login_url(self.request.uri))
                return
        if not users.is_current_user_admin():
            self.error(403)
        else:
            return method(self, *args, **kwargs)
    return wrapper

def render(handler,tname,tvalues):
    template = env.get_template(tname)
    handler.response.out.write(template.render(tvalues))
    
def cache_render(tname,tvalues):
    template = env.get_template(tname)
    return template.render(tvalues)

def locale_render(handler,lang,tname,tvalues):
    if lang == 'tr':
        render(handler, lang+'_'+tname, tvalues)
    else:
        render(handler, tname, tvalues)

def locale_cache_render(lang,tname,tvalues):
    if lang == 'tr':
    	template = env.get_template(lang+'_'+tname)
    else:
    	template = env.get_template(tname)
    return template.render(tvalues)

def refreshFeed(langcode):
    entries = db.Query(Entry).filter('draft =',False).filter('language =',langcode).order('-published').fetch(limit=5)
    feed_template_values = { 'entries': entries, 'now': datetime.datetime.now(), 'lang': langcode, }
    feed_page = cache_render("atom.xml", feed_template_values)
    memcache.set(langcode+"_feed",feed_page)
    return feed_page

class RootHandler(webapp.RequestHandler):
    def get(self):
        self.redirect('/en', permanent=True)

class MainPageHandler(webapp.RequestHandler):
    def get(self, lang):
        is_admin = users.is_current_user_admin()
	if not is_admin:
		main_page = memcache.get(lang+"_main")
		if main_page:
			self.response.out.write(main_page)
			return

        entries = db.Query(Entry).filter('draft =',False).filter('language =',lang).order('-published').fetch(limit=5)
        template_values = { 'entries': entries, 'selectedPage': 'home', 'is_admin': is_admin, }
        main_page = locale_cache_render(lang,'main.html',template_values)
	if not is_admin:
		memcache.set(lang+"_main",main_page)
	self.response.out.write(main_page)
		
class IndexHandler(webapp.RequestHandler):
    def get(self, lang):
        is_admin = users.is_current_user_admin()
	if not is_admin:
		entries = db.Query(Entry).filter('draft =',False).filter('language =',lang).order('-published').fetch(limit=100)
	else:
		entries = db.Query(Entry).filter('language =',lang).order('-published').fetch(limit=100)
	template_values = { 'entries': entries, 'selectedPage': 'index', }
	locale_render(self,lang,'index.html',template_values)

class EntryHandler(webapp.RequestHandler):
    def get(self, lang, slug):
        is_admin = users.is_current_user_admin()
	if not is_admin:
		entry_page = memcache.get(slug,namespace="entry")
		if entry_page:
        		self.response.out.write(entry_page)
			return
		
        entry = db.Query(Entry).filter('slug =', slug).get()
        if not entry:
            self.error(404)
        template_values = { 'entry': entry, 'is_admin': is_admin, }
        entry_page = locale_cache_render(lang,'entry.html',template_values)
	if not is_admin:
		memcache.set(slug,entry_page,namespace="entry")
        self.response.out.write(entry_page)
		
		
class EntryDeleteHandler(webapp.RequestHandler):
    @administrator
    def get(self,lang,slug):
        entry = db.Query(Entry).filter("slug =", slug).get()
        if not entry:
            self.error(404)
        locale_render(self,lang,"del.html", {'entry': entry, })
        
    @administrator
    def post(self,lang,slug):
        entry = db.Query(Entry).filter("slug =", slug).get()
        if not entry:
            self.error(404)
        delete = self.request.get('del')
        if delete and delete.upper() == 'Y':
	    memcache.delete(slug,namespace="entry")	# may need to retry in case returns 0 = network error
	    memcache.delete(lang+"_main")	# main may need to be refreshed
            entry.delete()
            refreshFeed(lang)   # refresh Feed upon delete
        self.redirect('/'+lang+'/index')


class EntryPublishHandler(webapp.RequestHandler):
    @administrator
    def get(self,lang,slug):
        entry = db.Query(Entry).filter("slug =", slug).get()
        if not entry:
            self.error(404)
	entry.draft = not entry.draft
	if not entry.draft:
		entry.published = datetime.datetime.now()
        entry.put()
        refreshFeed(lang)   # refresh Feed upon publishing
	memcache.delete(slug,namespace="entry")
	memcache.delete(lang+"_main")	# main may need to be refreshed
        self.redirect(entry.url())

def to_html(body):
    body_html = markdown2.markdown(body)
    return body_html


class NewEntryHandler(webapp.RequestHandler):
    @administrator
    def get(self,lang,slug=None):
        if slug:
            entry = db.Query(Entry).filter("slug =", slug).get()
            if not entry:
                self.error(404)
            else:
                lang = entry.language
            template_values = { 'entry': entry, }
        else:
            template_values = { 'entry': False, }
            
        locale_render(self,lang,"entry_edit.html", template_values)

    @administrator
    def post(self,lang,slug=None):
        author = users.get_current_user()
    	title = self.request.get('title')
    	slug = utils.slugify(title)
    	markdown = self.request.get('markdown')
    	body_html = to_html(markdown)
    	soup = BeautifulSoup.BeautifulSoup(body_html)
    	paras = soup.findAll('p')
        language = self.request.get('language')
        
        if paras:
	    strParas = [i.encode('utf8') for i in paras[:2]]
            excerpt = '\n'.join(strParas) + '\n...\n'
	    excerpt = excerpt.decode('utf8')
        else: excerpt = ''
        
        entry = db.Query(Entry).filter("slug =", slug).get()
        if not entry:
            entry = Entry(
                author=author,
                title=title,
                slug=slug,
                body_html=body_html,
                markdown=markdown,
                excerpt=excerpt,
                language=language,
            )
        else:
            entry.title = title
            entry.markdown = markdown
            entry.body_html = body_html
            entry.excerpt = excerpt
        entry.put()
        refreshFeed(language)   # refresh Feed upon save
	memcache.delete(slug,namespace="entry")
	memcache.delete(lang+"_main")	# main page must be refreshed
        self.redirect(entry.url())
        
class FeedHandler(webapp.RequestHandler):
    def get(self,lang):
        if lang == 'tr':
            feed_page = memcache.get("tr_feed")
        else:
            feed_page = memcache.get("en_feed")
        if not feed_page:
            feed_page = refreshFeed(lang)
        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.response.out.write(feed_page)

class AboutHandler(webapp.RequestHandler):
    def get(self,lang):
        if lang == 'tr':
            about_page = memcache.get("tr_about")
        else:
            about_page = memcache.get("en_about")

	if about_page:
            self.response.out.write(about_page)
	    return

        about_page = locale_cache_render(lang,'about.html',{'selectedPage': 'about'})
	memcache.set(lang+"_about",about_page)

        self.response.out.write(about_page)

class SitemapHandler(webapp.RequestHandler):
    def get(self):
	entries = db.Query(Entry).filter('draft =',False).order('-published').fetch(limit=5)
        template_values = { 'entries': entries }
        sitemap_page = cache_render("sitemap.xml",template_values)
	self.response.out.write(sitemap_page)
