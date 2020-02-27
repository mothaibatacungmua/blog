import click
from fxqu4nt.utils.csv_tick_file import CsvTickFile

@click.command()
@click.option('--file', help="Input .csv file")
@click.option('--mode', default='year', help='Mode to split')
def csv_split(file, mode):
    click.echo(file + " " + mode)


@click.command()
@click.option('--file', help="Input .csv file")
@click.option('--lines', help="Number of lines to display")
def csv_head(file, lines):
    csv_tick = CsvTickFile(file)
    click.echo(csv_tick.head(lines))


@click.command()
@click.option('--file', help="Input .csv file")
@click.option('--lines', help="Number of lines to display")
def csv_tail(file, lines):
    csv_tick = CsvTickFile(file)
    click.echo(csv_tick.tail(lines))