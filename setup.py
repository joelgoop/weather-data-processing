from setuptools import setup

setup(
    name='weather-process',
    version='0.1',
    py_modules=['process_wdata'],
    packages=['windpower'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        prow=process_wdata:cli
    ''',
)