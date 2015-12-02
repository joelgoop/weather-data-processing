import netCDF4 as nc
import numpy as np
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

import windpower.tradewind as tw

LAEA_EUROPE = {'width':3600000,'height':4500000,'projection':'laea',
                    'lat_ts':0,'lat_0':54,'lon_0':8.5}

def plt_map(lon,lat,data):
    m = Basemap(resolution='l',**LAEA_EUROPE)
    x, y = m(lon, lat)
    plt.figure(figsize=(20,20))
    m.drawcoastlines()
    # m.drawparallels(np.arange(-80.,81.,20.))
    # m.drawmeridians(np.arange(-180.,181.,20.))
    m.drawmapboundary(fill_color='white')
    m.contourf(x,y,data,levels=np.arange(0,0.6,0.01), extend="both");
    plt.colorbar( orientation='horizontal', pad=0.05)

infile = r'E:\data\weather\ecmwf\u-v_lvl59_reanalysis_2012.netcdf'
data = nc.Dataset(infile,'r')

# Create time index based on data in file
base_time = dt.datetime.strptime('1900-01-01 00:00','%Y-%m-%d %H:%M')
actual_time =  [base_time + dt.timedelta(hours=t) for t in data.variables['time']]
time_idx = pd.to_datetime(actual_time).to_period(freq='H')

# Create lat/long meshgrid
lat,lon = np.meshgrid(data.variables['latitude'][:],data.variables['longitude'][:])

u = data.variables['u'][:,:,:]
v = data.variables['v'][:,:,:]
print data.variables.keys()

abs_ws = np.sqrt(np.square(u)+np.square(v))
print abs_ws.shape

plt_map(lon.T,lat.T,np.mean(tw.offshore_future(abs_ws),axis=0))

plt.gcf().savefig('fig/offshore.png',dpi=500,bbox_inches='tight')