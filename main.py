#!/usr/bin/python
# -*- coding: utf-8 -*-

import turing
from google.appengine.ext.webapp.util import run_wsgi_app

def main():
	run_wsgi_app(turing.application)

if __name__ == '__main__':
	main()
