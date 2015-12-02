# -*- coding: utf-8 -*-
import click
import logging, logging.config

logger = logging.getLogger(__name__)


@click.group(help='process weather data to calculate vRES production and potential')
@click.option('--debug',is_flag=True,help='Show debug messages.')
def cli(debug):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level,
                        format="%(asctime)s [%(levelname)-8s] %(message)s",
                        datefmt="%H:%M:%S")

@cli.command(help='calculate vRES production from weather data')
@click.argument('datasource',type=click.Choice(['merra']),default='merra')
@click.argument('datatype',type=click.Choice(['wind', 'solar']))
@click.option('--source','-s',type=click.Path(exists=True,file_okay=False),required=True)
@click.option('--dest','-d',type=click.Path(exists=True,file_okay=False),required=True)
@click.option('--powercurve','-pc',type=click.Choice(['tw_lowland','tw_highland','tw_offshore']),required=True,default='tw_lowland')
@click.option('--extrap-method','-ex',type=click.Choice(['powerlaw','loglaw']),required=True,default='powerlaw')
def production(datasource,datatype,**kwargs):
    if datasource=='merra':
        if datatype=='wind':
            import windpower.merra

            logger.info('Processing wind data from MERRA.')
            windpower.merra.production(**kwargs)
        else:
            logger.error('Unknown data type!')
    else:
        logger.error('Unknown data source!')


@cli.command('prep-gis',help='preparatory GIS calculations')
@click.argument('datasource',type=click.Choice(['merra']),default='merra')
@click.option('--source','-s',type=click.Path(exists=True,file_okay=False),required=True)
@click.option('--dest','-d',type=click.Path(exists=True,file_okay=False),required=True)
@click.option('--exclude-dir','-e',type=click.Path(exists=True,file_okay=False),required=False)
@click.option('--extrap-method','-ex',type=click.Choice(['powerlaw','loglaw']),required=True,default='powerlaw')
def prepare_gis(datasource,datatype,**kwargs):
    if datasource=='merra':
        if datatype=='wind':
            import windpower.merra

            logger.info('Processing wind data from MERRA.')
            windpower.merra.production(**kwargs)
        else:
            logger.error('Unknown data type!')
    else:
        logger.error('Unknown data source!')


@cli.command(help='match sites regions and exclude protected')
@click.argument('datasource',type=click.Choice(['merra']),default='merra')
@click.option('--source','-s',type=click.Path(exists=True,file_okay=False),required=True)
@click.option('--dest','-d',type=click.Path(exists=True,file_okay=False),required=True)
@click.option('--exclude-dir','-e',type=click.Path(exists=True,file_okay=False),required=False)
@click.option('--extrap-method','-ex',type=click.Choice(['powerlaw','loglaw']),required=True,default='powerlaw')
def matchsites(datasource,datatype,**kwargs):
    if datasource=='merra':
        if datatype=='wind':
            import windpower.merra

            logger.info('Processing wind data from MERRA.')
            windpower.merra.production(**kwargs)
        else:
            logger.error('Unknown data type!')
    else:
        logger.error('Unknown data source!')


@cli.command(help='create some helpful plots')
@click.option('--source','-s',type=click.Path(exists=True,dir_okay=False),required=True)
@click.option('--savefile','-f',type=click.Path(dir_okay=False),required=False)
@click.option('--plottype','-p',type=click.Choice(['mean','timestep']),required=True,default='mean')
@click.option('--timestep','-t',type=int,required=False)
@click.option('--key','-k',type=str,required=True,default='wp_output_100m')
def plot(source,plottype,timestep,key,savefile,**kwargs):
    import plotting

    if timestep is None and plottype=='timestep':
        logger.error('Timestep plot chosen, but no timestep given.')
    if timestep is not None and plottype!='timestep':
        logger.error('Timestep plot not chosen, but timestep given.')

    fig,ax = plotting.plt_from_file(source,key,plottype,timestep)
    if savefile is not None:
        fig.savefig(savefile,dpi=500,bbox_inches='tight')
    else:
        plt.show()

    