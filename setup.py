from setuptools import setup, find_packages

setup(
    name='sonar-telegram',
    description='simple telegran client to interact with sonar',
    version='0.1',
    packages=find_packages(),
    license='MIT',
    py_modules=['sonar-telegram', 'telethon'],
    install_requires=[
        'Click',
        ],
    url='http://github.com/osuiowq/sonar-telegram',
    author='osuiowq / arso-project',
    author_email='_',
    zip_safe=False,
    entry_points='''
        [console_scripts]
        sonar-telegram=sonar_telegram:cli
    '''
    )
