import os
import sys
from setuptools import setup, find_packages

CURR_DIR = os.path.abspath(os.path.dirname(__file__))
INSTALL_REQUIRES = [
    "PyYAML>=5.1",
    "requests>=2.14.2",
]
with open(os.path.join(CURR_DIR, "README.md"), encoding="utf-8") as file_open:
    LONG_DESCRIPTION = file_open.read()

exec(open("qtrade/_version.py").read())

setup(
    name="qtrade",
    version=__version__,
    description="Questrade API wrapper for Python",
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url="https://github.com/jborchma/qtrade",
    license="MIT",
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    zip_safe=False,
)
