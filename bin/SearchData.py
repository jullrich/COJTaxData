#!/usr/bin/env python3

from lxml import html
import requests
import sys
import mysql.connector
import configparser

config=configparser.ConfigParser()
config.read('../etc/cojdata.ini')

url = 'https://paopropertysearch.coj.net/Basic/'

session = requests.Session()

try:
    page=requests.get(url+'Search.aspx')
except requests.exceptions.HTTPError as err:
    print(e)
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(e)
    sys.exit(1)
    
tree = html.fromstring(page.text)
form = tree.forms[0].fields


data={}
for key in form:
    data[key]=form[key]

# adjust here the paramters you would like to submit

data['ctl00$cphBody$tbZipCode']='32206'

# oddly enough, this can't be small (<25). can be as larger as 10,000
data['ctl00$cphBody$ddResultsPerPage']='100'


page = requests.post(url+'Results.aspx',data)
tree = html.fromstring(page.text)
tabledata=(tree.xpath('//table/tr/td//text()'))
line=0
column=0
searchline=[]
searchresults=[]
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
    


sql = 'insert ignore into searchresults (re6,re4,ownername, streetnumber, streetname, streettype, direction, unit, city,zip) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'

for td in tabledata:
    if td=='\xa0':
        td=''
    searchline.append(td)
    column=column+1
    if column==9:
        line=line+1
        column=0
        reparts=searchline[0].split('-')
        reparts.extend(searchline[1:])
        for i in range(len(reparts)):
            reparts[i]=str(reparts[i])
        try:
            mycursor.execute(sql,reparts)

        except MySQLdb.Error as e:
            print("mysql error [%d]: %s" % (e.args[0], e.args[1]))
        searchline=[]
mycursor.close()
mydb.commit()
mydb.close()
print("%d Lines Inserted" % (line) )
