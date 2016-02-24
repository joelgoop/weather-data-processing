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
@click.option('--datasource','-ds',
                type=click.Choice(['merra','merra2']),
                default='merra',
                help='the origin of the data')
def wind_production(dest,datasource,powercurve,extrap_method,hubheight,**kwargs):
    kwargs['powercurve'] = POWER_CURVES[powercurve]

    if 'merra' in datasource:
        import windpower.merra
        import h5py
        extrapolator = windpower.merra.EXTRAPOLATORS[extrap_method]
        kwargs['extrapolate'] = extrapolator(hubheight)

        logger.info('Processing wind data from {}.'.format(datasource.upper()))
        for year,lats,longs,time,ws_z,wp_output in windpower.merra.production(**kwargs):
            outfile_path = os.path.join(dest,
                                        'windpower_output.{}.{}.{}m.{}.{}.hdf5'.format(datasource,
                                                                                        extrap_method,
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

@cli.command('create-grid',help='create spatial grid and save to db')
@click.option('--lat-long-file','-l',type=click.Path(exists=True,dir_okay=False),required=True)
@click.option('--spatial-db','-s',type=click.Path(dir_okay=False),required=True)
@click.option('--dll-path','-dp',type=click.Path(exists=True,file_okay=False),default=r'D:\venvs\weather-data\DLLs')
def create_grid(lat_long_file,spatial_db,dll_path,**kwargs):
    import gis.calculations
    import gis.data
    import h5py
    import numpy as np

    logger.info('Reading lat/long data.')
    with h5py.File(lat_long_file,'r') as f:
        y,x = f['latitude'][:],f['longitude'][:]

    logger.info('Creating grid polygons.')
    polys = gis.calculations.create_grid_polygons(x,y)

    logger.info('Creating db table.')
    conn = gis.data.connect_spatial_db(spatial_db,dll_path)
    gis.data.drop_table(conn,'grid')
    gis.data.create_spatial_table(conn,'grid',4326,'POLYGON',
        other_cols=[('row','INTEGER'),('col','INTEGER'),('long','REAL'),('lat','REAL')])

    logger.info('Inserting polygons.')
    cur = conn.cursor()
    sql = "INSERT INTO grid (row,col,long,lat,geometry) VALUES (?,?,?,?,GeomFromText(?,4326))"
    logger.debug("SQL:\n"+sql)
    cur.executemany(sql,polys)
    conn.commit()
    conn.close()


@cli.command('create-classes',help='create wind classes for each region')
@click.option('--spatial-db','-db',
                help='path to spatial database',
                type=click.Path(exists=True,dir_okay=False),
                required=True)
@click.option('--source','-s',
                help='path to wind production folder',
                type=click.Path(exists=True,file_okay=False),
                required=True)
@click.option('--dest','-d',
                help='directory to save wind class data',
                type=click.Path(exists=True,file_okay=False),
                required=True)
@click.option('--dll-path','-dp',
                help='path to spatialite extension DLLs',
                type=click.Path(exists=True,file_okay=False),
                default=r'D:\venvs\weather-data\DLLs')
@click.option('--wind-key','-wk',
                help='key to read wind production data from file',
                type=str,
                default='wp_output')
def create_classes(spatial_db,dll_path,source,dest,wind_key,**kwargs):
    import gis.calculations
    import gis.data
    import windpower.classes
    import windpower.windio
    import re
    import os

    # Extract input settings from filename
    source_base = os.path.basename(source)
    input_settings = re.match(r'[^.]+\.(?P<fn>.+)\.hdf',source_base).group('fn')

    logger.info('Calculating intersections between grid and regions.')
    conn = gis.data.connect_spatial_db(spatial_db,dll_path)
    intersections = gis.calculations.get_intersections(conn,**kwargs)

    logger.info('Construct classes and calculate areas for each region.')
    logger.debug('Reading wind production data from file.')
    site_utilization = windpower.windio.get_flat_mean_output(source,wind_key)

    # Class calculations
    class_areas,class_utils,site_fractions = windpower.classes.class_areas(intersections,site_utilization)

    # Check class results
    if class_areas.shape != class_utils.shape:
        logger.error('Different shapes returned.')
        raise ValueError('Areas is {} by {}, util is {} by {}.'.format(*(class_areas.shape+class_utils.shape)))
    elif any(class_areas.index != class_utils.index) or \
            any(class_areas.columns != class_utils.columns):
        logger.error('Non-matching indices returned.')
        raise ValueError('Index or columns not matching between class_areas and class_utils.')


    outfile_path = os.path.join(dest,'wind_classes.{}.hdf'.format(input_settings))
    logger.info('Saving classes to {}.'.format(outfile_path))
    windpower.windio.write_classes_to_file(outfile_path,class_areas,class_utils,site_fractions)



@cli.command('calc-areas',help='calculate areas for each site per region')
@click.option('--spatial-db','-db',
                help='path to spatial database',
                type=click.Path(exists=True,dir_okay=False),
                required=True)
@click.option('--dest','-d',
                help='file to save areas and fractions',
                type=click.Path(exists=False,dir_okay=False),
                required=True)
@click.option('--dll-path','-dp',
                help='path to spatialite extension DLLs',
                type=click.Path(exists=True,file_okay=False),
                default=r'D:\venvs\weather-data\DLLs')
@click.option('--grid-table','-gt',
                help='name of table containing grid',
                type=str,
                default='merra_grid')
@click.option('--regions-table','-rt',
                help='name of table containing regions',
                type=str,
                default='nuts2006')
def calc_areas(spatial_db,dll_path,dest,**kwargs):
    import gis.calculations
    import gis.data
    import windpower.classes
    import windpower.windio

    logger.info('Calculating intersections between grid and regions.')
    conn = gis.data.connect_spatial_db(spatial_db,dll_path)
    intersections = gis.calculations.get_intersections(conn,**kwargs)

    logger.info('Creating area matrices.')
    site_areas,site_fractions = windpower.classes.site_areas_fractions(intersections)
    windpower.windio.write_areas_to_file(dest,site_areas,site_fractions)


@cli.command(help='create some helpful plots')
@click.option('--source','-s',type=click.Path(exists=True,dir_okay=False),required=True)
@click.option('--savefile','-f',type=click.Path(dir_okay=False),required=False)
@click.option('--plottype','-p',type=click.Choice(['mean','timestep']),default='mean')
@click.option('--timestep','-t',type=int,required=False)
@click.option('--key','-k',type=str,default=('wp_output',),multiple=True)
def plot(source,plottype,timestep,key,savefile,**kwargs):
    import plotting.map
    # import h5py
    # with h5py.File(source,'r') as f:
    #     for key in f:
    #         print key
    # exit()

    if timestep is None and plottype=='timestep':
        logger.error('Timestep plot chosen, but no timestep given.')
    if timestep is not None and plottype!='timestep':
        logger.error('Timestep plot not chosen, but timestep given.')

    fig,ax = plotting.map.plt_from_file(source,key,plottype,timestep)
    if savefile is not None:
        fig.savefig(savefile,bbox_inches='tight')
    else:
        plt.show()

    