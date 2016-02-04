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
    sql = """SELECT gid, rid,SUM(AREA(ST_Intersection(rgeom,geom)))/AREA(geom) AS overlap
FROM 
(SELECT TRANSFORM(r.geometry,:1) AS ngeom,TRANSFORM(g.geometry,:1) as geom,g.id AS gid,r.NUTS_ID AS rid
    FROM {grid_table} AS g, {regions_table} as r  
    WHERE r.STAT_LEVL_=2 AND g.ROWID IN (
            SELECT ROWID 
            FROM SpatialIndex
            WHERE f_table_name = 'merra_grid' 
                AND search_frame = TRANSFORM(rgeom,:2))
    AND ST_Intersects(geom,rgeom))
GROUP BY rid,gid
ORDER BY gid""".format(grid_table=u.quote_identifier(grid_table),regions_table=u.quote_identifier(regions_table))
    
    c = sdb_conn.cursor()

    logger.info("Calculating grid/regions intersections from spatial data.")
    logger.debug("SQL:\n"+sql)
    result = c.execute(sql, (reg_proj,grid_proj))

    intersections = {}
    for gid,rid,overlap in result:
        intersections[]






