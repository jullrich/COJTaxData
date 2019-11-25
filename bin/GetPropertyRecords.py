#!/usr/bin/env python3

from lxml import html
import requests
import sys
import mysql.connector
import configparser
import os

config=configparser.ConfigParser()
config.read('../etc/cojdata.ini')
url = 'https://paopropertysearch.coj.net/Basic/Detail.aspx?RE='
cachedir=config['cojdata']['DataCacheDir']
if not( os.path.isdir(cachedir)):
   print("cache directory %s does not exist" % (cachedir))
   sys.exit(1)
try:
   mydb=mysql.connector.connect(
   host=config['cojdata']['mysqlhost'],
   user=config['cojdata']['mysqluser'],
   database=config['cojdata']['mysqldatabase'],
   passwd=config['cojdata']['mysqlpass'],
   charset='utf8',
   use_unicode=True
   )
   mycursor=mydb.cursor()
except MySQLdb.Error as e:
   print("mysql error [%d]: %s" % (e.args[0], e.args[1]))
    
sql = 'select re6, re4 from searchresults'
mycursor.execute(sql)
while True:
      row=mycursor.fetchone();
      if row == None:
         break
      re="{:06d}{:04d}".format(row[0],row[1])
      filename=cachedir+'/'+re
      if not(os.path.isfile(filename)):
         page=requests.get(url+re)
         f=open(filename,"w")
         f.write(page.text)
         f.close()



 
   


