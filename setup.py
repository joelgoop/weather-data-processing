from setuptools import setup

setup(
    name='weather-process',
    version='0.1',
    packages=['prow'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        prow=prow.main:cli
    ''',
)