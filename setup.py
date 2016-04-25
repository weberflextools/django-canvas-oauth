import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as v_file:
    version = v_file.read().strip()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='canvas-oauth',
    version=version,
    packages=['canvas_oauth'],
    include_package_data=True,
    license="License :: OSI Approved :: MIT License",
    description='A reusable Django app used to handle OAuth2 flow with Canvas.',
    long_description=README,
    url='https://www.example.com/',
    author='Jaime Bermudez',
    author_email='tlt-ops@g.harvard.edu',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
