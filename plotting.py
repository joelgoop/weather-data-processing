import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import h5py
import logging

logger = logging.getLogger(__name__)

LAEA_EUROPE = {'width':3600000,'height':4500000,'projection':'laea',
                    'lat_ts':0,'lat_0':54,'lon_0':8.5}

def plt_map(lon,lat,data):
    m = Basemap(resolution='l',**LAEA_EUROPE)
    x, y = m(lon, lat)
    plt.figure(figsize=(20,20))
    m.drawcoastlines()
    m.drawmapboundary(fill_color='white')
    m.contourf(x,y,data,levels=np.arange(0,np.max(np.max(data)),0.01), extend="both");
    plt.colorbar( orientation='horizontal', pad=0.05)

def plt_from_file(fpath,key,plottype,timestep):
    with h5py.File(fpath) as f:
        lat,lon = np.meshgrid(f['latitude'][:],f['longitude'][:])
        if plottype=='mean':
            plt_map(lon.T,lat.T,np.mean(f[key],axis=0))
        elif plottype=='timestep':
            plt_map(lon.T,lat.T,f[key][timestep,:,:])
        else:
            logger.error('Unknown plot type!')
    

    return plt.gcf(),plt.gca()