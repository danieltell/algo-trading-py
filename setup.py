#!/usr/bin/env python

import setuptools
import os
import runpy

pkg_root = os.path.dirname(__file__)
__version__ = runpy.run_path(os.path.join(pkg_root, 'algotradingpy', '__init__.py') )['__version__']


setuptools.setup(

    name='algotradingpy',
    version=__version__,
    author="Daniel Antonio Tell",
    author_email="danieltell@gmail.com",
    description="AlgoTradingPy é uma biblioteca para backtesting e estratégias de negociação de criptomoeda.",
    long_description_content_type="text/markdown",
    url="https://github.com/danieltell/algotradingpy",
    packages=setuptools.find_packages(),
    install_requires=[
        'matplotlib>=3.0.3',
        'pandas>=1.5.0',
        'numpy>=1.18.1',
        'mpl-finance>=0.10.1',
        "requests==2.24.0",
        'mysql_connector==2.2.9'
        ],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Algorithmic Trading',
        'Topic :: Software Development',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        ],
    python_requires='>=3.6',
 )
