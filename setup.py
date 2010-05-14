from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='rpz.websocket',
      version=version,
      description="Real time web support for repoze",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Ben Ford',
      author_email='ben@boothead.co.uk',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['rpz'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'repoze.bfg',
          'eventlet'
          # -*- Extra requirements: -*-
      ],
      entry_points = {
      'paste.server_factory': ['eventlet_server = rpz.websocket.factory:server_factory'],
      }
      )
