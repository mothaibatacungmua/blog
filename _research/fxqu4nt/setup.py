from setuptools import setup, find_packages

setup(
    name='fxqu4nt',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'click',
        'qpython==2.0.0',
        'PyQt5==5.13.0',
        'pandas==0.25.3',
        'pyqtgraph==0.10.0',
        'pyyaml'
    ],
    entry_points='''
        [console_scripts]
        csv_tick_split=fxqu4nt.cli.commands.csv_tick_file_command:csv_split
        csv_tick_head=fxqu4nt.cli.commands.csv_tick_file_command:csv_head
        csv_tick_tail=fxqu4nt.cli.commands.csv_tick_file_command:csv_tail
        csv_fix_date=fxqu4nt.cli.commands.csv_tick_file_command:csv_fix_date
    '''
)