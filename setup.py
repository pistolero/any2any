# coding=utf-8
#!/usr/bin/env python

from distutils.core import setup

setup(name='any2any',
      version='0.4.0',
      description='A Python library to write casts from any type to any other type.',
      author='Sébastien Piquemal',
      author_email='sebastien.piquemal@futurice.com',
      url='https://bitbucket.org/sebpiq/any2any',
      packages=['any2any'],
      license='BSD',
      classifiers=['Intended Audience :: Developers', 'Topic :: Utilities' ],
      long_description='any2any is a Python library for magically casting any type to any other type. It helps you with (de)serialization operations, formatting operations, any kind of transformation between two Python objects. It is highly and easily customizable, and provides facilities for debugging your transformations.',
     )
