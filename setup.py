from setuptools import setup, find_packages

setup(
    name='sonar-telegramclient',
    description='simple telegran client to interact with sonar',
    version='0.1',
    packages=find_packages(),
    license='MIT',
    py_modules=['sonar-telegramclient', 'telethon'],
    install_requires=[
        'Click',
        ],
    url='http://github.com/osuiowq/sonar-client-python',
    author='osuiowq / arso-project',
    author_email='_',
    zip_safe=False,
    entry_points='''
        [console_scripts]
        sonar-telegramclient=sonar_telegramclient:cli
    '''
    )
