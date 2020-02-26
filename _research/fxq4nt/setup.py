from setuptools import setup, find_packages

setup(
    name='fxq4nt',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        csv_tick_split=fxq4nt.cli.commands.csv_tick_file_command:csv_split
        csv_tick_head=fxq4nt.cli.commands.csv_tick_file_command:csv_head
        csv_tick_tail=fxq4nt.cli.commands.csv_tick_file_command:csv_tail
    '''
)