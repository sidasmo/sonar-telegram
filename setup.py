from setuptools import setup, find_packages

setup(
    name='sonar_telegram',
    description='simple telegran client to interact with sonar',
    version='0.1',
    packages=find_packages(),
    license='MIT',
    py_modules=['sonar_telegram_cli', 'sonar_telegram', 'json_encoder','telegram_api_credentials'],
    install_requires=[
        'Click',
        'aiohttp',
        'tika',
        'telethon',
        ],
    url='http://github.com/osuiowq/sonar-telegram',
    author='osuiowq / arso-project',
    author_email='_',
    zip_safe=False,
    entry_points='''
        [console_scripts]
        sonar_telegram=sonar_telegram_cli:cli
    '''
    )
