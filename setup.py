from setuptools import setup, find_packages

DESCRIPTION = 'Transforms HAML to Tornado templates or Underscore.js'

with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()

VERSION = '0.1.0'

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(name='haiku',
    version=VERSION,
    packages=find_packages(),
    author='Stanislav Vishnevskiy',
    author_email='vishnevskiy@gmail.com',
    url='https://github.com/vishnevskiy/haiku',
    license='MIT',
    include_package_data=True,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    classifiers=CLASSIFIERS,
    test_suite='tests',
)