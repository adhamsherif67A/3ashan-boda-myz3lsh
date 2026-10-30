from glob import glob
from setuptools import setup
setup(name='mako_pool_mapping',version='0.1.0',packages=['mako_pool_mapping'],
 data_files=[('share/ament_index/resource_index/packages',['resource/mako_pool_mapping']),
 ('share/mako_pool_mapping',['package.xml']),
 ('share/mako_pool_mapping/launch',glob('launch/*.launch.py')),
 ('share/mako_pool_mapping/config',glob('config/*'))],
 install_requires=['setuptools'],zip_safe=True,
 entry_points={'console_scripts':[
 'loop_evidence=mako_pool_mapping.evidence:main',
 'drive_pool_loop=mako_pool_mapping.drive_loop:main']})
