# -*- coding: utf-8 -*-
import click
import logging, logging.config
import windpower.tradewind
import os

logger = logging.getLogger(__name__)

POWER_CURVES = {
    'tw_lowland': windpower.tradewind.lowland_future,
    'tw_highland': windpower.tradewind.upland_future,
    'tw_offshore': windpower.tradewind.offshore_future
}

@click.group(help='process weather data to calculate vRES production and potential')
@click.option('--debug',is_flag=True,help='Show debug messages.')
def cli(debug):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level,
                        format="%(asctime)s [%(levelname)-8s] %(message)s",
                        datefmt="%H:%M:%S")

@cli.command('wind-production',help='calculate vRES production from weather data')
@click.option('--source','-s',type=click.Path(exists=True,file_okay=False),required=True)
@click.option('--dest','-d',type=click.Path(exists=True,file_okay=False),required=True)
@click.option('--powercurve','-pc',type=click.Choice(POWER_CURVES.keys()),default='tw_lowland')
@click.option('--extrap-method','-ex',type=click.Choice(['powerlaw','loglaw']),default='powerlaw')
@click.option('--hubheight','-z',type=float,default=100.)
@click.option('--datasource',
                type=click.Choice(['merra']),
                default='merra',
                help='the origin of the data')
def wind_production(dest,datasource,powercurve,extrap_method,hubheight,**kwargs):
    kwargs['powercurve'] = POWER_CURVES[powercurve]

    if datasource=='merra':
        import windpower.merra
        import h5py
        extrapolator = windpower.merra.EXTRAPOLATORS[extrap_method]
        kwargs['extrapolate'] = extrapolator(hubheight)

        logger.info('Processing wind data from MERRA.')
        for year,lats,longs,time,ws_z,wp_output in windpower.merra.production(**kwargs):
            outfile_path = os.path.join(dest,
                                        'windpower_output.merra.{}.{}m.{}.{}.hdf5'.format(extrap_method,
                                                                                          int(hubheight),
                                                                                          powercurve,
                                                                                          year))
            logger.debug('Trying to open h5 file {}.'.format(outfile_path))
            with h5py.File(outfile_path,'w') as outfile:
                logger.info('Saving to file {}.'.format(outfile_path))
                outfile['longitude'] = longs
                outfile['latitude'] = lats
                outfile['time'] = time
                outfile['ws_{}m'.format(int(hubheight))] = ws_z
                outfile['wp_output'] = wp_output
    else:
        logger.error('Unknown data source!')


@cli.command('prep-gis',help='preparatory GIS calculations')
@click.option('--spatial-db','-s',type=click.Path(exists=True,dir_okay=False),required=True)
@click.option('--dll-path','-dp',type=click.Path(exists=True,file_okay=False),required=True,default=r'D:\venvs\weather-data\DLLs')
def prepare_gis(spatial_db,dll_path,**kwargs):
    # import gis.calculations
    # import gis.data
    # import windpower.classes

    # logger.info('Calculating intersections between grid and regions.')
    # conn,gis.data.connect_spatial_db('C:/data_tmp/gis/test-gis.sqlite',dll_path)
    # intersections = gis.calculations.get_intersections(conn,**kwargs)
    # print intersections
    logger.error('Not implemented!')


@cli.command('create-classes',help='create wind classes for each region')
@click.option('--spatial-db','-s',
                help='path to spatial database',
                type=click.Path(exists=True,dir_okay=False),
                required=True)
@click.option('--dll-path','-dp',
                help='path to spatialite extension DLLs',
                type=click.Path(exists=True,file_okay=False),
                default=r'D:\venvs\weather-data\DLLs')
@click.option('--wind-key','-wp',
                help='path to wind production HDF file',
                type=click.Path(exists=True,dir_okay=False),
                required=True)
def create_classes(spatial_db,dll_path,wind_data,**kwargs):
    print kwargs
    import gis.calculations
    import gis.data

    logger.info('Calculating intersections between grid and regions.')
    conn = gis.data.connect_spatial_db(spatial_db,dll_path)
    intersections = gis.calculations.get_intersections(conn,**kwargs)


@cli.command(help='create some helpful plots')
@click.option('--source','-s',type=click.Path(exists=True,dir_okay=False),required=True)
@click.option('--savefile','-f',type=click.Path(dir_okay=False),required=False)
@click.option('--plottype','-p',type=click.Choice(['mean','timestep']),required=True,default='mean')
@click.option('--timestep','-t',type=int,required=False)
@click.option('--key','-k',type=str,required=True,default='wp_output_100m')
def plot(source,plottype,timestep,key,savefile,**kwargs):
    import plotting.map

    if timestep is None and plottype=='timestep':
        logger.error('Timestep plot chosen, but no timestep given.')
    if timestep is not None and plottype!='timestep':
        logger.error('Timestep plot not chosen, but timestep given.')

    fig,ax = plotting.map.plt_from_file(source,key,plottype,timestep)
    if savefile is not None:
        fig.savefig(savefile,bbox_inches='tight')
    else:
        plt.show()

    