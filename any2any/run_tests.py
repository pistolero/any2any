#!/usr/bin/env python
from nose import run
print """
######################################################################
TESTING MODULES
"""
run(argv=['dummy', '--exclude-dir=djangocast_tests'])

print """
----------------------------------------------------------------------
TESTING djangostack
"""
import os
from django.core import management
from djangocast_tests import settings
saved_path = os.getcwd()
os.chdir('djangocast_tests')
management.execute_manager(settings, argv=['dummy', 'test', 'test_models'])
os.chdir(saved_path)

print """
######################################################################
TESTING DOCUMENTATION
"""

run(argv=['dummy', '--tests=../../docs/doc_pages/base.rst,../../docs/doc_pages/djangocast.rst', '--with-doctest', '--doctest-extension=rst'])
