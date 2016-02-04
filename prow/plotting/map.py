import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import h5py
import logging

logger = logging.getLogger(__name__)

LAEA_EUROPE = {'width':3600000,'height':4500000,'projection':'laea',
                    'lat_ts':0,'lat_0':54,'lon_0':8.5}

def plt_map(lon,lat,data):
    """
    Plot data on a map from lat/long and a data array (m x n).

    Args:
        lon: m x n matrix with longitude values
        lat: m x n matrix with latitude values
        data: m x n matrix with data values

    Returns:
        tuple: figure and axis object with plot
    """
    logger.debug("Creating Basemap for {} by {} data with {} NaNs.".format(data.shape[0],data.shape[1],np.count_nonzero(np.isnan(data))))
    m = Basemap(resolution='l',**LAEA_EUROPE)

    logger.debug("Preparing figure.")

    # Transform coordinates 
    x, y = m(lon, lat)

    # Create figure and draw map base
    fig,ax = plt.subplots(figsize=(20,20))
    m.drawcoastlines()
    m.drawmapboundary(fill_color='white')

    # Create levels for contour
    dmax = np.nanmax(np.nanmax(data))
    levels = np.arange(0,dmax,0.01)
    logger.debug("Drawing contour from data with {} levels (between 0 and {}).".format(len(levels),dmax))

    m.contourf(x,y,data,levels=levels, extend="both");
    plt.colorbar( orientation='horizontal', pad=0.05)
    return fig,ax

def plt_from_file(fpath,key,plottype,timestep):
    """
    Retrieve data and call plt_map with right arguments depending on plot type.

    Args:
        fpath: path to data file
        key: key to retrieve data by
        plottype: type of plot ('timestep' or 'mean')
        timestep: timestep to plot (if plottype=='timestep')

    Returns:
        tuple: figure and axis object with plot
    """
    logger.info("Plotting {} of {} from {}".format(plottype,key,fpath))
    with h5py.File(fpath) as f:
        lat,lon = np.meshgrid(f['latitude'][:],f['longitude'][:])
        if plottype=='mean':
            fig,ax = plt_map(lon.T,lat.T,np.mean(f[key],axis=0))
        elif plottype=='timestep':
            fig,ax = plt_map(lon.T,lat.T,f[key][timestep,:,:])
        else:
            logger.error('Unknown plot type!')
    

    return fig,ax