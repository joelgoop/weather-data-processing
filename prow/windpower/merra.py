# -*- coding: utf-8 -*-
import numpy as np
from extrapolation import log_law,power_law
import logging
import os
import glob
import re

logger = logging.getLogger(__name__)

def vectorize_merra_log_law(z):
    """
    Create 'vectorized' version of merra_log_law taking matrices of h, v2, and 
    v50 and returns extrapolated wind speed at z.

    Args:
        z (float): height above ground to extrapolate wind speed to
    """
    return np.vectorize(lambda h,v10,v50: merra_log_law(z,h,v10,v50))

def merra_log_law(z,h,v10,v50):
    """
    Uses log law extrapolation for MERRA data, using 10m data (10 meters above 
    displacement height) and 50m data (50 meters above surface).

    Args:
        z (float): height to extrapolate to (above surface)
        h (float): displacement height
        v10 (float): wind speed 10 m above displacement height
        v50 (float): wind speed 50 m above surface

    Returns:
        float: extrapolated wind speed at height z above surface
    """
    return log_law(z,h,(10.0,v10),(50.0-h,v50))

def vectorize_merra_power_law(z):
    """
    Create 'vectorized' version of merra_power_law taking matrices of h, v2, and 
    v50 and returns extrapolated wind speed at z.

    Args:
        z (float): height above ground to extrapolate wind speed to
    """
    return np.vectorize(lambda h,v10,v50: merra_power_law(z,h,v10,v50))

def merra_power_law(z,h,v10,v50):
    """
    Uses power law extrapolation for MERRA data, using 10m data (10 meters above 
    displacement height) and 50m data (50 meters above surface).

    Args:
        z (float): height to extrapolate to (above surface)
        h (float): displacement height
        v10 (float): wind speed 10 m above displacement height
        v50 (float): wind speed 50 m above surface

    Returns:
        float: extrapolated wind speed at height z above surface
    """
    return power_law(z,h,(10.0,v10),(50.0-h,v50))

EXTRAPOLATORS = {
    'loglaw':vectorize_merra_log_law,
    'powrelaw': vectorize_merra_power_law
}

def production(source,dest,powercurve,extrapolate,**kwargs):
    """
    Transform MERRA wind speed data into wind power production time series.

    Args:
        source (str): path to source data file
        dest (str): path to destination folder
        powercurve (function): function to transform wind speed to output
        extrapolate (function): an extrapolator for MERRA data (h, ws10m, ws50m)
    """
    logger.debug('Entering production transformation function for MERRA wind.')
    import tradewind
    import h5py

    # Read data
    regex_y = re.compile(r'[^.]+\.(?P<year>\d{4})\.hdf')
    files = sorted(glob.glob(os.path.join(source,'*.hdf')))
    logger.debug('Searching through {} files in {}.'.format(len(files),source))
    if not files:
        logger.warning('No source files found in {}!'.format(source))
    for f in files:
        try:
            year = regex_y.match(f).group('year')
        except Exeption as e:
            logger.error('Could not extract year from {}.'.format(f))
            raise e

        logger.debug('Trying to open input file {}.'.format(f))
        with h5py.File(f,'r') as infile:
            logger.info('Reading variables from {}.'.format(f))
            h = np.array(infile['disph'])
            u10 = np.absolute(np.array(infile['u10m']))
            v10 = np.absolute(np.array(infile['v10m']))
            u50 = np.absolute(np.array(infile['u50m']))
            v50 = np.absolute(np.array(infile['v50m']))
            longs = np.array(infile['longitude'])
            lats = np.array(infile['latitude'])
            time = np.array(infile['time'])

        # Extrapolate wind speed to hub height
        logger.debug('Calculating vector magnitude of wind speeds.')
        abs_ws10 = np.sqrt(np.square(u10)+np.square(v10))
        abs_ws50 = np.sqrt(np.square(u50)+np.square(v50))
        logger.debug('Running extrapolation function.')
        abs_ws_z = extrapolate(h,abs_ws10,abs_ws50)

        # Apply the selected power curve
        logger.info("Applying power curve '{}'.".format(powercurve.__name__))
        wp_output = powercurve(abs_ws_z)

        outfile_path = os.path.join(dest,'windpower_output.merra.{}.{}m.{}.{}.hdf5'.format(extrap_method,int(z),powercurve,year))
        logger.debug('Trying to open h5 file {}.'.outfile_path)
        with h5py.File(outfile_path,'w') as outfile:
            logger.info('Saving to file {}.'.format(outfile_path))
            outfile['longitude'] = longs
            outfile['latitude'] = lats
            outfile['time'] = time
            outfile['ws_10m'] = abs_ws10
            outfile['ws_50m'] = abs_ws50
            outfile['ws_{}m'.format(int(z))] = abs_ws_z
            outfile['wp_output_{}m'.format(int(z))] = wp_output
