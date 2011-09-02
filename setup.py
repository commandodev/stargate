from setuptools import setup, find_packages
import os

version = '0.4'

setup(name='stargate',
      version=version,
      description="Real time communication for pyramid using WebSockets",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.rst")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Ben Ford',
      author_email='ben@boothead.co.uk',
      url='http://github.com/boothead/stargate',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'pyramid',
          'pyramid_zcml',
          'eventlet',
          'ws4py',
          # -*- Extra requirements: -*-
      ],
      test_suite='nose.collector',
      tests_require=[
        'nose',
        'mock',
      ],
      entry_points = {
      'paste.server_factory': ['eventlet_server = stargate.factory:server_factory'],
      }
      )
