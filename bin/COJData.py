from lxml import html
import requests
import mysql.connector
from mysql.connector import errorcode
import os.path
import sys


def re10tore64(re):
    re6 = re[0:6]
    re4 = re[6:]
    return re6 + '-' + re4


def re10tolist(re):
    relist = [re[0:6], re[6:]]
    return relist


class COJData:
    taxcollectorurl = 'https://fl-duval-taxcollector.publicaccessnow.com/PropertyTaxSearch/AccountDetail/BillDetail' \
                      '.aspx?p= '
    propertysearchurl = 'https://paopropertysearch.coj.net/Basic/Detail.aspx?RE='
    searchurl = 'https://paopropertysearch.coj.net/Basic/Search.aspx'
    resulturl = 'https://paopropertysearch.coj.net/Basic/Results.aspx'
    taxoverviewurl = 'https://fl-duval-taxcollector.publicaccessnow.com/propertytaxsearch/accountdetail.aspx?p='
    taxbillurl = 'https://fl-duval-taxcollector.publicaccessnow.com/PropertyTaxSearch/AccountDetail/BillDetail.aspx?p='
    config = {}
    cachedir = ''
    session = ''
    dbh = None
    cursor = None

    def __init__(self, config):
        self.config = config
        self.cachedir = config['cojdata']['DataCacheDir']

    def check_cache(self, re, suffix):
        filename = self.cache_file(re, suffix)
        if os.path.isfile(filename):
            return True
        return False

    def get(self, url):
        page = None
        if self.session == '':
            self.session = requests.session()

        # user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36
        # (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        # headers = {'User-Agent': user_agent}

        try:
            page = self.session.get(url)
            page.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            sys.exit(1)
        except requests.exceptions.Timeout:
            print("Timeout Error retreiving " + url)
            sys.exit(1)
        except requests.exceptions.TooManyRedirects:
            print("Too many redirects retrieving " + url)
        except requests.exceptions.RequestException as err:
            print("Catastrophic Error ")
            print(err)
            sys.exit(1)
        return page

    def get_property_record(self, re):
        if self.check_cache(re, 'pr'):
            return True
        page = self.get(self.propertysearchurl + re)
        self.save_file(page, re, 'pr')
        return True

    def post(self, url, params):
        page = None
        if self.session == '':
            self.session = requests.session()
        try:
            page = self.session.post(url, params)
            page.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            sys.exit(1)
        except requests.exceptions.Timeout:
            print("Timeout Error retreiving " + url)
            sys.exit(1)
        except requests.exceptions.TooManyRedirects:
            print("Too many redirects retrieving " + url)
        except requests.exceptions.RequestException as err:
            print("Catastrophic Error ")
            print(err)
            sys.exit(1)
        return page

    def search(self, searchdata, limit):
        if limit < 25:
            limit = 25
        if limit > 50000:
            limit = 50000

        self.db_connect()

        page = self.get(self.searchurl)
        tree = html.fromstring(page.text)
        form = tree.forms[0].fields
        data = {}
        for key in form:
            data[key] = form[key]
        for key in searchdata:
            data[key] = searchdata[key]
        data['ctl00$cphBody$ddResultsPerPage'] = str(limit)
        data['ctl00$cphBody$idBasicAddAddressToExport'] = ''
        page = self.post(self.resulturl, data)
        tree = html.fromstring(page.text)
        tabledata = (tree.xpath('//table/tr/td//text()'))
        mycursor = self.dbh.cursor()
        sql = 'insert ignore into searchresults (re6,re4,ownername, streetnumber, streetname, streettype, direction, ' \
              'unit, city,zip) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
        lines = 0
        columns = 0
        searchline = []
        for td in tabledata:
            if td == '\xa0':
                td = ''
            searchline.append(td)
            columns = columns + 1
            if columns == 9:
                lines = lines + 1
                columns = 0
                reparts = searchline[0].split('-')
                reparts.extend(searchline[1:])
                for i in range(len(reparts)):
                    reparts[i] = str(reparts[i])
                mycursor.execute(sql, reparts)
                searchline = []
        mycursor.close()
        self.dbh.commit()
        self.dbh.close()
        return lines

    def db_connect(self):
        if not (self.dbh is None):
            return True
        try:
            self.dbh = mysql.connector.connect(
                host=self.config['cojdata']['mysqlhost'],
                user=self.config['cojdata']['mysqluser'],
                database=self.config['cojdata']['mysqldatabase'],
                passwd=self.config['cojdata']['mysqlpass'],
                charset='utf8',
                use_unicode=True
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Could not connect to database. Username/password Error")
                print(err)
                sys.exit(1)
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
                sys.exit(1)
            else:
                print(err)
                sys.exit(1)
        return True

    def cache_file(self, re, suffix):
        dir1 = re[2:4]
        dir2 = re[4:6]
        if not (os.path.isdir(self.cachedir + '/' + dir1)):
            os.mkdir(self.cachedir + '/' + dir1)
        if not (os.path.isdir(self.cachedir + '/' + dir1 + '/' + dir2)):
            os.mkdir(self.cachedir + '/' + dir1 + '/' + dir2)
        return self.cachedir + '/' + dir1 + '/' + dir2 + '/' + re + suffix

    def save_file(self, page, re, suffix):
        filename = self.cache_file(re, suffix)
        f = open(filename, 'w')
        f.write(page)

    def read_file(self, re, suffix):
        filename = self.cache_file(re, suffix)
        if not os.path.isfile(filename):
            return False
        f = open(filename, 'r')
        text = f.read()
        f.close()
        return text

    def get_property_records_query(self, query):
        self.get_db_cursor()
        self.cursor.execute(query)
        records = 0
        recordswritten = 0
        while True:
            row = self.cursor.fetchone()
            if row is None:
                break
            records = records + 1
            re = "{:06d}{:04d}".format(row[0], row[1])
            if not (self.check_cache(re, 'pr')):
                recordswritten = recordswritten + 1
                page = requests.get(self.propertysearchurl + re)
                self.save_file(page.text, re, 'pr')
        print("Total Records: %d Records Written: %d" % (records, recordswritten))
        return True

    def get_tax_data_query(self, query):
        self.get_db_cursor()
        self.cursor.execute(query)
        records = 0
        while True:
            row = self.cursor.fetchone()
            if row is None:
                break
            records = records + 1
            re = "{:06d}{:04d}".format(row[0], row[1])
            self.get_tax_overview(re)
            self.parse_tax_overview(re)
        print("Total Records: %d")

    def get_tax_overview(self, re):
        if self.check_cache(re, 'to'):
            return True
        page = self.get(self.taxoverviewurl + re10tore64(re))
        self.save_file(page.text, re, 'to')
        return True

    def get_db_cursor(self):
        if not (self.cursor is None):
            return True
        self.db_connect()
        try:
            self.cursor = self.dbh.cursor()
        except mysql.connector.Error as err:
            print("Unable to get cursor. ", format(err))
            sys.exit(1)
        return True

    def sql_execute(self, sql, data):
        self.get_db_cursor()
        try:
            self.cursor.execute(sql, data)
        except mysql.connector.Error as err:
            print("Could not execute SQL. Error: ", format(err))
            print("SQL Statement: %s" % sql)
            print("Parameters: %s" % data)
            sys.exit(1)
        return True

    def parse_tax_overview(self, re):
        page = self.read_file(re, 'to')
        tree = html.fromstring(page)
        tabledata = tree.xpath('//div[@id="443"]/table/tbody/tr/td//text()')
        columns = 0
        lines = 0
        billline = re10tolist(re)
        sql = 'insert ignore into taxbills (re6, re4, year, folio, ownername, amountdue) values (%s,%s,%s,%s,%s,%s)'
        for td in tabledata:
            billline.append(td.replace('$', ''))
            columns = columns + 1
            if columns == 4:
                lines = lines + 1
                columns = 0
                self.sql_execute(sql, billline)
                self.get_tax_bill(re, billline[3], billline[2])
                self.parse_tax_bill(re, billline[3], billline[2])
                billline = re10tolist(re)
        return lines

    def get_tax_bill(self, re, folio, year):
        if self.check_cache(re + '-' + folio + '-' + year, 'tb'):
            return True
        page = self.get(self.taxbillurl + re10tore64(re) + '&b=' + folio + '&y=' + year)
        self.save_file(page.text, re + '-' + folio + '-' + year, 'tb')
        return True

    def parse_tax_bill(self, re, folio, year):
        page = self.read_file(re + '-' + folio + '-' + year, 'tb')
        tree = html.fromstring(page)
        self.db_connect()
        self.dbh.cursor()
        columns = 0
        lines = 0
        billline = re10tolist(re)
        billline.append(year)
        billline.append(folio)
        sql = 'insert ignore into taxbilldetails ' + \
              '(re6, re4, year, folio, taxingcode, taxingauthority, assessedvalue, exemptionamount, taxablevalue,' + \
              ' millagerate, taxes) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        tabledata = tree.xpath('//div[@id="lxT500"]/table/tr/td//text()')
        for td in tabledata:
            billline.append(td.replace('$', '').replace('\n', '').replace(',', '').replace('\t', ''))
            columns = columns + 1
            if columns == 7:
                lines = lines + 1
                columns = 0
                self.cursor.execute(sql, billline)
                billline = re10tolist(re)
                billline.append(year)
                billline.append(folio)
        self.dbh.commit()
        sql = 'update taxbills set taxes=%s where re6=%s and re4=%s and folio=%s and year=%s'
        self.cursor.execute(sql, (billline[8], billline[0], billline[1], billline[3], billline[2]))
        self.dbh.commit()
        billline = re10tolist(re)
        billline.append(year)
        billline.append(folio)
        columns = 0
        sql = 'insert ignore into taxbillfeedetails ' + \
              '(re6, re4, year, folio, feecode, feeauthority, fees) values (%s, %s, %s, %s, %s, %s, %s)'
        tabledata = tree.xpath('//div[@id="lxT501"]/table/tr/td//text()')
        for td in tabledata:
            billline.append(td.replace('$', '').replace('\n', '').replace(',', '').replace('\t', ''))
            columns = columns + 1
            if columns == 3:
                lines = lines + 1
                columns = 0
                self.cursor.execute(sql, billline)
                billline = re10tolist(re)
                billline.append(year)
                billline.append(folio)
        sql = 'update taxbills set fees=%s where re6=%s and re4=%s and folio=%s and year=%s'
        if len(billline) == 5:
            self.cursor.execute(sql, (billline[4], billline[0], billline[1], billline[3], billline[2]))
        self.dbh.commit()
        return lines