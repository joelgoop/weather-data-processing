# -*- coding: utf-8 -*-
from scipy.interpolate import interp1d
import numpy as np

# Based on TradeWind deliverable D2.4
# WP2.6 – Equivalent Wind Power Curves
windspeeds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
# Normalised output in % based on 'Table 2.3 Future regional normalised power curve models for 2030'
output_percent = {
    'offshore': [0, 0, 0, 1, 2, 5, 8, 14, 20, 29, 40, 53, 64, 76, 84, 89, 89, 89, 89, 89, 89, 89, 89, 89, 89, 83, 71, 54, 36, 18, 6, 0, 0, 0, 0, 0],
    'lowland': [0, 0, 1, 2, 4, 8, 14, 22, 33, 48, 62, 75, 85, 92, 94, 94, 94, 94, 94, 94, 94, 94, 94, 94, 90, 83, 72, 56, 38, 23, 11, 4, 0, 0, 0, 0],
    'upland': [0, 1, 2, 5, 8, 13, 20, 29, 39, 49, 59, 68, 77, 84, 89, 93, 94, 94, 94, 94, 94, 94, 92, 88, 82, 73, 63, 52, 42, 31, 21, 13, 6, 2, 0, 0]
}
# Create interpolating functions
interp_args = {'kind': 'linear','bounds_error': False, 'fill_value': 0}
output_fcn = {key: interp1d(windspeeds,np.array(output_vals)/100.0,**interp_args) for key,output_vals in output_percent.iteritems()}

def power(ws,key):
    return output_fcn[key](ws)

def lowland_future(ws):
    """Regional power curve function for future lowland wind power."""
    return power(ws,'lowland')

def upland_future(ws):
    """Regional power curve function for future upland wind power."""
    return power(ws,'upland')

def offshore_future(ws):
    """Regional power curve function for future offshore wind power."""
    return power(ws,'offshore')


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    xs = np.linspace(max(windspeeds)+2,min(windspeeds),500)
    ll = lowland_future(xs)
    ul = upland_future(xs)
    os = offshore_future(xs)

    plt.plot(xs,ll,xs,ul,xs,os)
    plt.legend(['lowland','upland','offshore'])
    plt.show()