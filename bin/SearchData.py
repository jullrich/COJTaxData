#!/usr/bin/env python3

import configparser
from COJData import COJData

config = configparser.ConfigParser()
config.read('../etc/cojdata.ini')
cachedir = config['cojdata']['DataCacheDir']
# adjust here the paramters you would like to submit

data = {'ctl00$cphBody$tbRE6': '',
        'ctl00$cphBody$tbRE4': '',
        'ctl00$cphBody$tbName': '',
        'ctl00$cphBody$tbStreetNumber': '',
        'ctl00$cphBody$tbStreetName': '',
        'ctl00$cphBody$ddStreetSuffix': '',
        'ctl00$cphBody$ddStreetPrefix:': '',
        'ctl00$cphBody$tbStreetUnit': '',
        'ctl00$cphBody$ddCity': '',
        'ctl00$cphBody$tbZipCode': '32209'}

coj = COJData(config)
lines = coj.search(data, 50)
print("%d Lines Inserted" % lines)
