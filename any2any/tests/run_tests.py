#!/usr/bin/env python
from nose import run
import os
os.chdir('..')
print """
######################################################################
TESTING MODULES
"""
run(argv=['dummy'])

#print """
######################################################################
#TESTING DOCUMENTATION
#"""

#run(argv=['dummy', '--tests=../../docs/doc_pages/base.rst,../../docs/doc_pages/djangocast.rst', '--with-doctest', '--doctest-extension=rst'])
