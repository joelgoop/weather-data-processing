import h5py
import numpy as np
import logging

logger = logging.getLogger(__name__)

def write_classes_to_file(outfile_path,class_areas,class_utils,site_fractions):
    """
    Write output from wind class calculations to hdf5 file.

    Args:
        outfile_path (str): path to hdf5 output file
        class_areas (pandas.DataFrame): areas in each class for each region
        class_utils (pandas.DataFrame): utilization factor for each class in 
            each region
        site_fractions (pandas.Panel): fraction of each site's contribution to
            each class in each region
    """
    with h5py.File(outfile_path,'w') as outfile:
        logger.debug('Saving indices.')
        outfile['regions'] = np.array(class_areas.index,dtype=str)
        outfile['classes'] = np.array(class_areas.columns,dtype=float)
        outfile['sites'] = np.array(site_fractions.major_axis,dtype=int)

        logger.debug('Saving data.')
        util_ds = outfile.create_dataset('utilization',dtype=float,
            shape=class_utils.shape,fillvalue=float('nan'),
            compression='gzip',compression_opts=9)
        util_ds[:] = class_utils
        util_ds.attrs['dim1'] = 'regions'
        util_ds.attrs['dim2'] = 'classes'

        area_ds = outfile.create_dataset('areas',dtype=float,
            shape=class_areas.shape,fillvalue=float('nan'),compression='gzip',
            compression_opts=9)
        area_ds[:] = class_areas
        area_ds.attrs['dim1'] = 'regions'
        area_ds.attrs['dim2'] = 'classes'

        site_fraction_ds = outfile.create_dataset('site_fractions',dtype=float,
            shape=site_fractions.shape,fillvalue=float('nan'),compression='gzip',
            compression_opts=9)
        site_fraction_ds[:] = site_fractions
        site_fraction_ds.attrs['dim1'] = 'regions'
        site_fraction_ds.attrs['dim2'] = 'sites'
        site_fraction_ds.attrs['dim3'] = 'classes'


def write_areas_to_file(outfile_path,site_areas,site_fractions):
    """
    Save site areas and fractions to HDF5 file.

    Args:
        outfile_path: path to output file
        site_areas (pandas.DataFrame): N by M dataframe with area intersection 
            between site and region where N is number of sites and M number of 
            regions
        site_fractions (pandas.DataFrame): N by M dataframe with each site's 
            contribution to each region
    """

    with h5py.File(outfile_path,'w') as f:
        logger.debug('Saving indices.')
        f['regions'] = np.array(site_fractions.columns,dtype=str)
        f['sites'] = np.array(site_fractions.index,dtype=int)

        logger.debug('Creating datasets.')
        areas_ds = f.create_dataset('areas',dtype=float,
            shape=site_areas.shape,fillvalue=float('nan'),
            compression='gzip',compression_opts=9)
        fractions_ds = f.create_dataset('fractions',dtype=float,
            shape=site_fractions.shape,fillvalue=float('nan'),
            compression='gzip',compression_opts=9)

        logger.debug('Saving data.')
        areas_ds[:] = site_areas
        areas_ds.attrs['dim1'] = 'sites'
        areas_ds.attrs['dim2'] = 'regions'

        fractions_ds[:] = site_fractions
        fractions_ds.attrs['dim1'] = 'sites'
        fractions_ds.attrs['dim2'] = 'regions'


def get_flat_mean_output(source,key):
    """
    Read and flatten mean wind power production from hdf5 file.

    Args:
        source (str): path to source hdf5 file
        key (str): key to dataset to read

    Returns:
        numpy.ndarray: 1d vector with average site utilization
    """
    with h5py.File(source,'r') as f:
        site_matrix = np.mean(f[key],axis=0)
        site_utilization = site_matrix.flatten()
        logger.debug('Sites is a {} by {} matrix.'.format(*site_matrix.shape))

        row = site_matrix[0,:]
        flattened_start = site_utilization[:site_matrix.shape[1]]
        del site_matrix
        if not np.count_nonzero(flattened_start-row)==0:
            logger.error('First elements of flattened not equal to matrix row.')
            raise ValueError('Flattened:\n{}\nRow:\n{}'.format(
                            flattened_start,row))
    return site_utilization