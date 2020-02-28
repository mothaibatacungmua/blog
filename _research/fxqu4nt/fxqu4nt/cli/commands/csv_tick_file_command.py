import click
from fxqu4nt.utils.csv_tick_file import CsvTickFile

@click.command()
@click.option('--file', help="Input .csv file")
@click.option('--mode', default='year', help='Mode to split')
@click.option('--out_dir', default='.', help="Output directory to save")
def csv_split(file, mode, out_dir):
    csv_tick = CsvTickFile(file)
    csv_tick.split(mode, out_dir=out_dir)

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