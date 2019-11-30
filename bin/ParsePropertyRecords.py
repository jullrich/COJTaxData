#!/usr/bin/env python3

#  <span id="ctl00_cphBody_lblRealEstateNumber">045437-0000</span>
# <div id="details_trimExtended" class="dt_header">


import mysql.connector
from lxml import html
import configparser
import os
import sys

re = sys.argv[1]
print(re)
config = configparser.ConfigParser()
config.read('../etc/cojdata.ini')
cachedir = config['cojdata']['DataCacheDir']
filename = cachedir + '/' + re
if not (os.path.isfile(filename)):
    print("File not found %s" % filename)
    sys.exit(1)
f = open(filename, 'r')
text = f.read()
f.close()
tree = html.fromstring(text)
redata = tree.xpath('//span[@id="ctl00_cphBody_lblRealEstateNumber"]/text()')[0]
reparts = redata.split('-')
zoning = tree.xpath('//table[@id="ctl00_cphBody_gridLand"]/tr/td//text()')[3]
year = tree.xpath('//span[@id="ctl00_cphBody_lblHeaderCertified"]//text()')[0].split(' ')[0]
valuemethod = tree.xpath('//span[@id="ctl00_cphBody_lblValueMethodCertified"]//text()')[0]
buildingvalue = tree.xpath(
    '//span[@id="ctl00_cphBody_lblBuildingValueCertified"]//text()')[0].replace('$', '').replace(',', '')
landvaluemarket = tree.xpath(
    '//span[@id="ctl00_cphBody_lblLandValueMarketCertified"]//text()')[0].replace('$', '').replace(',', '')
landvalueagric = tree.xpath(
    '//span[@id="ctl00_cphBody_lblLandValueAgricultureCertified"]//text()')[0].replace('$', '').replace(
    ',', '')
justmarketvalue = tree.xpath(
    '//span[@id="ctl00_cphBody_lblJustMarketValueCertified"]//text()')[0].replace('$', '').replace(',', '')
assessedvalue = tree.xpath(
    '//span[@id="ctl00_cphBody_lblAssessedValueA10Certified"]//text()')[0].replace('$', '').replace(',', '')
exemptions = tree.xpath(
    '//span[@id="ctl00_cphBody_lblExemptValueCertified"]//text()')[0].replace('$', '').replace(',', '')
taxablevalue = tree.xpath(
    '//span[@id="ctl00_cphBody_lblTaxableValueCertified"]//text()')[0].replace('$', '').replace(',', '')

print("%s %s %s %s %s %s %s %s %s %s" % \
      (redata, year, valuemethod, buildingvalue, landvaluemarket, landvalueagric, justmarketvalue, assessedvalue,
       exemptions, taxablevalue))
mydb = mysql.connector.connect(
    host=config['cojdata']['mysqlhost'],
    user=config['cojdata']['mysqluser'],
    database=config['cojdata']['mysqldatabase'],
    passwd=config['cojdata']['mysqlpass'],
    charset='utf8',
    use_unicode=True
)
mycursor = mydb.cursor()
sql = 'insert ignore into taxrecord (re6,re4,year, valuemethod, buildingvalue, landvaluemarket, landvalueagric, ' + \
    'justmarketvalue, assessedvalue, exemptions, taxablevalue,zoning) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
v = (str(reparts[0]), str(reparts[1]), str(year), str(valuemethod), str(buildingvalue), str(landvaluemarket),
     str(landvalueagric), str(justmarketvalue), str(assessedvalue), str(exemptions), str(taxablevalue), str(zoning))
print(v)
mycursor.execute(sql, v)
mycursor.close()
mydb.commit()
mydb.close()
