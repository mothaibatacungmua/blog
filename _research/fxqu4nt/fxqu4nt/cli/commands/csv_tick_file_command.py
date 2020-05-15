import click
from fxqu4nt.utils.csv_tick_file import *

@click.command()
@click.option('--file', help="Input .csv file")
@click.option('--mode', default='year', help='Mode to split')
@click.option('--out_dir', default='.', help="Output directory to save")
def csv_split(file, mode, out_dir):
    split(file, mode, out_dir=out_dir)

@click.command()
@click.option('--file', help="Input .csv file")
@click.option('--lines', help="Number of lines to display", type=int)
def csv_head(file, lines):
    click.echo(head(file, lines))


@click.command()
@click.option('--file', help="Input .csv file")
@click.option('--lines', help="Number of lines to display", type=int)
def csv_tail(file, lines):
    click.echo(tail(file, lines))


@click.command()
@click.option('--file', help="Input .csv file")
def csv_fix_date(file):
    click.echo("Fixing incorrect datetime")
    fix_date(file)
    click.echo("Done!")