#!/usr/bin/env python
from nose import run
import os
os.chdir('..')
print """
######################################################################
TESTING MODULES
"""
run(argv=['dummy', '--exclude-dir=django/tests/'])

print """
----------------------------------------------------------------------
TESTING django
"""
from django.core import management
from any2any.django.tests import settings
saved_path = os.getcwd()
os.chdir('django/tests/')
management.execute_manager(settings, argv=['dummy', 'test'])
os.chdir(saved_path)

#print """
######################################################################
#TESTING DOCUMENTATION
#"""

#run(argv=['dummy', '--tests=../../docs/doc_pages/base.rst,../../docs/doc_pages/djangocast.rst', '--with-doctest', '--doctest-extension=rst'])
