# adapted over https://github.com/pypa/sampleproject/blob/master/setup.py

from setuptools import setup, find_packages
from os import path
import timefliptt

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

with open(path.join(here, 'requirements.in')) as f:
    requirements = f.readlines()

setup(
    name='timeflip-tt',
    version=timefliptt.__version__,

    # Description
    description=timefliptt.__doc__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='website',

    project_urls={
        'Bug Reports': 'https://github.com/pierre-24/timefliptt/issues',
        'Source': 'https://github.com/pierre-24/timefliptt/',
    },

    author='Pierre Beaujean',

    # Classifiers
    classifiers=[
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions:
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],

    packages=find_packages(),
    python_requires='>=3.8',

    include_package_data=True,

    # requirements
    install_requires=requirements,

    entry_points={
        'console_scripts': [
            'timeflip-tt = timefliptt.app:main',
        ]
    },
)
