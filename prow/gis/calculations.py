import prow.gis.data as gisdata
import logging
import prow.utils as u

logger = logging.getLogger(__name__)

def get_intersections(sdb_conn, regions_table='nuts2006', grid_table='merra_grid', reg_proj=3035, grid_proj=4326):
    """
    Calculate area of intersections between regions and grid cells.

    Args:
        sdb_conn: connection object to spatial database
        regions_table: name of table containing region geometries (default 'nuts2006')
        grid_table: name of table containing grid geometries (default 'merra_grid')
        reg_proj: projection SRID for regions' projection (default 3035 (European LAEA))
        grid_proj: projection SRID for grid's projection (default 4326 (lat/long))

    Returns:
        dict: areas of intersecting grid cells for each region
            e.g. {'reg1': {'grid_cell1': area1, 'grid_cell2': area1, ...}, ...}
    """
    sql = """SELECT gid, rid,SUM(AREA(ST_Intersection(rgeom,ggeom))) AS overlap
FROM 
(SELECT TRANSFORM(r.geometry,:1) AS rgeom,TRANSFORM(g.geometry,:1) as ggeom,g.id AS gid,r.NUTS_ID AS rid
    FROM {grid_table} AS g, {regions_table} as r  
    WHERE r.STAT_LEVL_=2 AND g.ROWID IN (
            SELECT ROWID 
            FROM SpatialIndex
            WHERE f_table_name = {grid_table} 
                AND search_frame = TRANSFORM(rgeom,:2))
    AND ST_Intersects(ggeom,rgeom))
GROUP BY rid,gid
ORDER BY gid""".format(grid_table=u.quote_identifier(grid_table),regions_table=u.quote_identifier(regions_table))
    
    c = sdb_conn.cursor()

    logger.info("Calculating grid/regions intersections from spatial data.")
    logger.debug("SQL:\n"+sql)
    result = c.execute(sql, (reg_proj,grid_proj))

    logger.debug("Creating dictionary.")
    intersections = u.multilevel_dict()
    for gid,rid,overlap in result:
        intersections[rid][gid] = overlap

    return intersections


def create_grid_polygons(x,y):
    """
    Creates a list of grid polygons (rectangles) in well-known text (WKT) format from evenly spaced x and y vectors.

    Args:
        x (1d numpy array): vector of x-values
        y (1d numpy array): vector of y-values

    Returns:
        list: grid polygons in WKT format
    """
    import numpy as np
    import pdb

    xdiff = np.diff(x)
    if np.std(xdiff)>1e-10:
        raise ValueError('Uneven longitude spacing.')
    dx = np.mean(xdiff)

    ydiff = np.diff(y)
    if np.std(ydiff)>1e-10:
        raise ValueError('Uneven latitude spacing.')
    dy = np.mean(ydiff)

    logger.debug('Spacing is ({},{})'.format(dx,dy))
    xmatr,ymatr = np.meshgrid(x,y)

    rows = []
    for (i,j),x_ij in np.ndenumerate(xmatr):
        y_ij = ymatr[i,j]
        x1,y1 = x_ij-dx/2.,y_ij-dy/2.
        x2,y2 = x_ij+dx/2.,y_ij+dy/2.
        rows.append((i,j,x_ij,y_ij,'POLYGON(({x1} {y1},{x1} {y2},{x2} {y2},{x2} {y1},{x1} {y1}))'.format(x1=x1,y1=y1,x2=x2,y2=y2)))

    return rows





