"""Setup file"""
import os
import re
import codecs
from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()
with open('requirements.txt.txt') as f:
    REQUIRED = f.read().splitlines()

def find_version():
    here = os.path.abspath(os.path.dirname(__file__))
    there = os.path.join(here, 'untrack.py')

    version_file = codecs.open(there, 'r').read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)

    else:
        raise RuntimeError("Unable to find version string.")

__version__ = find_version()

setup(
    name='untrack',
    version=__version__,
    install_requires=REQUIRED,
    packages=['.'],
    entry_points={
        'console_scripts': ['untrack=untrack:cli'],
    },
    include_package_data=True,
    license='BSD License',
    description='A cmd wrapper to untrack file of git',
    long_description=README,
    url='https://github.com/minghu6/untrack.git',
    author='minghu6',
    author_email='a19678zy@163.com',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System:: POSIX:: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)