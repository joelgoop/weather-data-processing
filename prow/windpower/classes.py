import prow.utils as u
import logging

logger = logging.getLogger(__name__)

def class_areas(site_areas,
                annual_utilization,
                class_limits=[0.35,0.3,0.25,0.2,0.175,0.15,0.125,0.1]):
    """
    Calculate areas per wind power class based on site areas, wind power 
    production and limits for utilization per class.

    Args:
        site_areas (dict): areas for each site in each region 
            e.g. {'reg1': {site_idx: area1, ...}, ...}
        annual_utilization (list/array): annual utilization factors for each 
            site
        class_limits (list): lower limits for utilization in each class

    Returns:
        tuple: areas for classes (per region), utilization factor for classes 
            (per region), and weights for each site (per region and class)
    """
    import pandas as pd

    # Create DataFrame from areas num_sites x num_regs
    logger.debug('Convert area dict to DataFrame.')
    area_df = pd.DataFrame.from_dict(site_areas)
    num_regs = area_df.shape[1]
    logger.debug('Area DF has {} sites and {} regions.'.format(*area_df.shape))

    # Create dataframe with utilization factors
    logger.debug('Construct utilization DataFrame.')
    u_series = pd.Series(annual_utilization)
    u_df = pd.concat([u_series]*num_regs,axis=1)
    u_df.columns = area_df.columns

    u_df = u_df.loc[area_df.index,:]

    logger.debug('Calculate areas in each class for each region.')
    pad_class_limits = [1.0]+class_limits+[0.0]
    class_areas = pd.DataFrame(index=area_df.columns,
                                columns=pad_class_limits[1:])
    class_utils = pd.DataFrame(index=area_df.columns,
                                columns=pad_class_limits[1:])
    site_fractions_dict = {}
     # = pd.Panel(items=area_df.columns,
     #                            major_axis=area_df.index,
     #                            minor_axis=pad_class_limits[1:])
    for ub,lb in u.pairwise(pad_class_limits):
        selection = ((area_df>0) & (u_df>lb) & (u_df<ub)).dropna()
        logger.debug('For class {} select {} elements.'.format(lb,
            selection.sum().sum()))

        class_areas[lb] = area_df[selection].sum()
        site_fractions_dict[lb] = area_df[selection]/class_areas[lb]
        # Area-weighted mean for class utilization 
        class_utils[lb] = (u_df[selection]*area_df[selection]).sum()/class_areas[lb]

    site_fractions = pd.Panel.from_dict(site_fractions_dict,orient='minor')

    return class_areas,class_utils,site_fractions

def site_areas_fractions(site_areas):
    """
    Calculate areas for each site in each region.

    Args:
        site_areas (dict): areas for each site in each region 
            e.g. {'reg1': {site_idx: area1, ...}, ...}

    Returns:
        tuple: areas for sites (per region), weights for each site (per region)
    """
    import pandas as pd

    # Create DataFrame from areas num_sites x num_regs
    logger.debug('Convert area dict to DataFrame.')
    area_df = pd.DataFrame.from_dict(site_areas)
    num_regs = area_df.shape[1]
    logger.debug('Area DF has {} sites and {} regions.'.format(*area_df.shape))

    return area_df,area_df/area_df.sum()