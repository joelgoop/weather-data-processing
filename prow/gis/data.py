import pysqlite2.dbapi2 as sqlite
import os
import logging
import prow.utils as u

logger = logging.getLogger(__name__)

GEOM_COL_TYPES = ['POLYGON','MULTIPOLYGON','POINT']
OTHER_COL_TYPES = ['REAL','INTEGER','TEXT','BLOB']

def copy_geoms(to_conn,to_table,from_db,from_tables,geom_col='geometry',
                calc_area_col='shape_area',**kwargs):
    """
    Copy geometries in 'from_tables' in 'from_db' into 'to_table' in 'to_conn'.

    Args:
        to_conn: target database connection object
        to_table: table to copy into
        from_db: path to original db
        from_tables: list of tables to copy
        geom_col: name of geometry column
        calc_area_col: name of column for calculated area (area not calculated
            if set to None)
    """
    # Escape input values
    esc_to_table = u.quote_identifier(to_table)
    esc_from_tables = map(u.quote_identifier,from_tables)
    esc_geom_col = u.quote_identifier(geom_col)

    create_spatial_table(to_conn,to_table,3035,'MULTIPOLYGON')

    print conn.execute("SELECT COUNT({}) FROM {} LIMIT 1".format(esc_geom_col,esc_to_table)).fetchall()


    # # Attach from_db and copy values
    # conn.execute('ATTACH ? AS source', (from_db,)).fetchone()
    # conn.execute('SELECT Area(geometry) FROM source.protected_polygons LIMIT 1').fetchone()


def drop_table(conn,table):
    """
    Drop table from database.

    Args:
        conn: database connection object
        table: name of table to drop
    """
    sql = 'DROP TABLE IF EXISTS {}'.format(u.quote_identifier(table))
    logger.debug("Drop table SQL:\n    '{}'".format(sql))
    logger.info('Dropping table {}'.format(table))
    conn.execute(sql)


def connect_spatial_db(path,dll_path):
    """
    Connect to a spatial db and init metadata (if not existing).

    Args:
        path: path to db file
        dll_path: path to mod_spatialite.dll
    """
    logger.debug("Connecting to db at '{}'".format(path))
    conn = sqlite.connect(path)
    conn.enable_load_extension(True)

    logger.info('Loading spatialite extension.')
    logger.debug("Looking for 'mod_spatialite.dll' in '{}' and PATH"\
                    .format(dll_path))
    with u.addpath(dll_path):
        conn.load_extension('mod_spatialite.dll')

    logger.info("Initializing spatial metadata.")
    conn.execute("BEGIN ;")
    conn.execute('SELECT InitSpatialMetaData()')
    conn.execute("COMMIT ;")

    return conn

def create_spatial_table(conn,tbl_name,srid,geom_type,other_cols=None,geom_col='geometry'):
    """
    Create a spatial table.

    Args:
        conn: database connection object
        tbl_name: name of new table
        srid: SRID of projection for new table
        geom_type: type of geometries in new table
        other_cols: sequence of tuples with (name,type) of additional columns
        geom_col: name of geometry column
    """

    geom_type = geom_type.upper()
    if geom_type not in GEOM_COL_TYPES:
        raise ValueError("Unknown geometry column type '{}'".format(geom_type))
    srid = int(srid)

    if other_cols:
        other_col_list = []
        other_col_sep = ', '
        for colname,coltype in other_cols:
            esc_name = u.quote_identifier(colname)
            coltype = coltype.upper()
            if coltype not in OTHER_COL_TYPES:
                raise ValueError("Unknown column type '{}'.".format(coltype))
            other_col_list.append(esc_name+' '+coltype)
        other_col_str = other_col_sep + other_col_sep.join(other_col_list)
    else:
        other_col_str = ''

    esc_tbl_name = u.quote_identifier(tbl_name)
    esc_geom_col = u.quote_identifier(geom_col)


    # Create table for geometries
    sql = 'CREATE TABLE IF NOT EXISTS {} ("id" INTEGER PRIMARY KEY ASC{})'\
            .format(esc_tbl_name,other_col_str)
    logger.debug("Table creation SQL:\n   '{}'".format(sql))
    logger.info("Creating table {}".format(esc_tbl_name))
    conn.execute(sql)

    sql = 'SELECT AddGeometryColumn({}, {}, {}, "{}", "XY")'\
            .format(esc_tbl_name,esc_geom_col,srid,geom_type)
    logger.debug("Geometry column creation SQL:\n   '{}'".format(sql))
    logger.info("Creating geometry column {}.".format(esc_geom_col))
    conn.execute(sql)




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s [%(levelname)-8s] %(message)s",
                        datefmt="%H:%M:%S")
    conn = connect_spatial_db(path='C:/data_tmp/gis/test-gis.sqlite',
                              dll_path='D:\\venvs\\weather-data\\DLLs')
    
    tab_name = 'test_table'
    drop_table(conn,tab_name)

    copy_geoms(conn,to_table=tab_name,
                from_db='C:/data_tmp/gis/europe-gis-data-copy',
                from_tables=['nuts2006'],
                calc_area_col=None)
    conn.close()
