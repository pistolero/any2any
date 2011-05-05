# coding=utf-8
#!/usr/bin/env python

from distutils.core import setup

setup(name='any2any',
      version='0.1',
      description='A library to write casts',
      author='Sébastien Piquemal',
      author_email='sebastien.piquemal@futurice.com',
      url='https://bitbucket.org/sebpiq/any2any',
      packages=['any2any', 'any2any.tests', 'any2any.tests.djangocast_tests', 'any2any.tests.djangocast_tests.models'],
      data_files=[
            ('.', ['LICENSE', 'README.rst']),
            ('docs', ['docs']),
      ]
     )

