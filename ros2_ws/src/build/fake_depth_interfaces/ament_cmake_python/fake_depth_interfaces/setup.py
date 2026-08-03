from setuptools import find_packages
from setuptools import setup

setup(
    name='fake_depth_interfaces',
    version='0.0.0',
    packages=find_packages(
        include=('fake_depth_interfaces', 'fake_depth_interfaces.*')),
)
