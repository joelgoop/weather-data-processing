import pysqlite2.dbapi2 as db
import os

os.environ['PATH']='D:\\venvs\\weather-data\\DLLs;'+os.environ['PATH']

conn = db.connect('C:/data_tmp/gis/europe-gis-data-copy.sqlite')
conn.enable_load_extension(True)
conn.load_extension('mod_spatialite.dll')

print conn.execute('SELECT Area(geometry) FROM protected_polygons LIMIT 1').fetchone()