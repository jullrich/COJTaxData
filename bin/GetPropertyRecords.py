#!/usr/bin/env python3

import configparser
from COJData import COJData

config = configparser.ConfigParser()
config.read('../etc/cojdata.ini')

cojdata = COJData(config)
dbh = cojdata.db_connect()
mycursor = dbh.cursor()
sql = "select re6, re4 from searchresults where zip='32209'"
cojdata.get_property_records_query(sql)
