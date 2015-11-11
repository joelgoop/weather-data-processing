import numpy as np
import logging

logger = logging.getLogger(__name__)

def log_law(z,h,hv1,hv2):
    """
    Extrapolate wind speed using logarithmic law v_z = A log((z-h)/z0), where A 
    is the (friction velocity)/(von Karman constant) and z0 is the roughness 
    length. Uses two known heights and wind speeds. 

    NB: Seems to encounter problems at some sites (small fraction <1e-4) with 
    exp overflow, divide by zero, etc.

    Args:
        z (float): height to extrapolate to (above ground)
        h (float): displacement height
        hv1 (tuple): first known height and wind speed as (h,v) where h is 
            height above displacement height and v is wind speed
        hv2 (tuple): second known height and wind speed

    Returns:
        float: extrapolated wind speed at z
    """
    h1,v1 = hv1
    h2,v2 = hv2

    z0 = np.exp((v1*np.log(h2) - v2*np.log(h1))/(v1-v2))
    A = v2 / np.log(h2/z0)

    return A*np.log((z-h)/z0)


def power_law(z,h,hv1,hv2):
    """
    Extrapolate wind speed using power law v_z = v_ref*((z-h)/z_ref)^alpha, 
    where h is displacement height and z_ref/v_ref is height (above displacement 
    height) and wind speed for a reference point. Uses two reference points to 
    estimate alpha.

    Args:
        z (float): height to extrapolate to (above ground)
        h (float): displacement height
        hv1 (tuple): first known height and wind speed as (h,v) where h is 
            height above displacement height and v is wind speed
        hv2 (tuple): second known height and wind speed

    Returns:
        float: extrapolated wind speed at z
    """
    h1,v1 = hv1
    h2,v2 = hv2

    alpha = (np.log(v2)-np.log(v1))/(np.log(h2)-np.log(h1))

    return v2*((z-h)/h2)**alpha
    