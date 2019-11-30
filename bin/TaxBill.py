#!/usr/bin/env python3

import configparser
from COJData import COJData

config = configparser.ConfigParser()
config.read('../etc/cojdata.ini')

cojdata = COJData(config)
cojdata.get_db_cursor()
sql='select re6, re4 from addresses where springfield="Y"'
cojdata.get_tax_data_query(sql)
# re='0719840000'
# cojdata.get_tax_overview(re)
# cojdata.parse_tax_overview(re)
