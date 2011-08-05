# coding=utf-8
#!/usr/bin/env python

from distutils.core import setup

setup(name='any2any',
      version='0.2',
      description='A Python library to write casts from any type to any other type (features Django serializers, ...)',
      author='Sébastien Piquemal',
      author_email='sebastien.piquemal@futurice.com',
      url='https://bitbucket.org/sebpiq/any2any',
      packages=['any2any', 'any2any.compat'],
      license='BSD',
      classifiers=['Intended Audience :: Developers', 'Framework :: Django', 'Topic :: Utilities' ],
      long_description='A Python library for magically casting any type (or format) to any other type (or format). any2any helps you with (de)serialization operations, formatting operations, any kind of transformation between two Python objects. any2any is highly and easily customizable, and provides facilities for debugging your transformations. A lot of casts are provided : for Django, ... ; and building blocks to create new ones.',
     )
