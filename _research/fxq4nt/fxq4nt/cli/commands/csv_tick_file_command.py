import click


@click.command()
@click.option('--file', help="Input .csv file")
@click.option('--mode', default='year', help='Mode to split')
def csv_split():
    click.echo('Call split')


@click.command()
@click.option('--input_file', help="Input .csv file")
def csv_head():
    click.echo('Call head')


@click.command()
@click.option('--input_file', help="Input .csv file")
def csv_tail():
    click.echo('Call tail')