from setuptools import setup, find_packages
import io
import os

import gpsr_command_understanding

here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


long_description = read('README.md')


setup(
    name='gpsr-command-understanding',
    version=gpsr_command_understanding.__version__,
    url='http://github.com/nickswalker/gpsr-command-understanding',
    license='MIT',
    author='Nick Walker',
    install_requires=['allennlp',
                      'lark-parser',

                      ],
    author_email='nswalker@cs.washington.edu',
    description='Automated REST APIs for existing database-driven systems',
    long_description=long_description,
    packages=['gpsr_command_understanding'],
    include_package_data=True,
    platforms='any',
    classifiers = [
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)