#!/usr/local/bin/python3
# encoding=utf-8

'''
Created on 01/mar/2014

@author: makeroo
'''

import datetime
import decimal
import gzip
import re
import sys
import traceback

import pymysql
from tornado import options as opt

import xml.etree.ElementTree as etree


def convertValue (v):
    '''Converte un import monetario GnuCash in Decimal.
    Esempio: '-560/100' -> decimal.Decimal('5.6')
    '''
    if v.startswith('-'):
        m = -1
        v = v[1:]
    else:
        m = 1
    x = v.split('/')
    if len(x) == 1:
        return m * decimal.Decimal(x[0])
    elif len(x) == 2:
        return m * decimal.Decimal(x[0]) / decimal.Decimal(x[1])
    else:
        raise Exception('unknown value', v)

def convertDate (d):
    '''Converte una data GnuCash in UTC.
    '''
    try:
        dt, tz = convertDate.fmt.match(d).groups()
        t = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        if tz is not None:
            h, m = int(tz[:3]), int(tz[3:])
            return t - datetime.timedelta(minutes = h * 60 + m)
        else:
            return t
    except:
        raise Exception('illegal date', d)

convertDate.fmt = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ?([+-]\d{4})?')

def xmlText (parent, childTag):
    e = parent.find(childTag)
    return e.text if e is not None else None

def xmlDate (parent, childTag):
    e = parent.find(childTag)
    d = e.find('{http://www.gnucash.org/XML/ts}date')
    # nel caso d non sia None, ignoro ns
    return convertDate(d.text if d is not None else e.text)

def gnucashId (parent, childTag, **kwargs):
    e = parent.find(childTag)
    if e is None:
        if 'default' in kwargs:
            return kwargs['default']
        else:
            raise Exception('missing tag', parent, childTag)
    if e.attrib.get('type', None) != 'guid':
        raise Exception('invalid id type', parent, e.attrib)
    return e.text

def dbText (s):
    return s #s.encode('utf8') if s is not None else None

class Account (object):
    def __init__ (self, accountElem):
        self.name = xmlText(accountElem, '{http://www.gnucash.org/XML/act}name')
        self.description = xmlText(accountElem, '{http://www.gnucash.org/XML/act}description')
        self.type = xmlText(accountElem, '{http://www.gnucash.org/XML/act}type')
        self.id = gnucashId(accountElem, '{http://www.gnucash.org/XML/act}id')
        self.parent = gnucashId(accountElem, '{http://www.gnucash.org/XML/act}parent', default=None)
        self.parentAccount = None # risolto dopo
        self.children = []
        self.saldo = decimal.Decimal(0)

    def __str__ (self):
        return '%s: %s' % (self.name, self.saldo)

class Transaction (object):
    def __init__ (self, transactionElem):
        self.id = gnucashId(transactionElem, '{http://www.gnucash.org/XML/trn}id')
        self.splits = [ Split(s) for s in transactionElem.findall('.//{http://www.gnucash.org/XML/trn}split')]
        self.date = xmlDate(transactionElem, '{http://www.gnucash.org/XML/trn}date-entered')
        self.description = xmlText(transactionElem, '{http://www.gnucash.org/XML/trn}description')

class Split (object):
    def __init__ (self, splitElem):
        self.id = gnucashId(splitElem, '{http://www.gnucash.org/XML/split}id')
        self.value = convertValue(splitElem.find('{http://www.gnucash.org/XML/split}value').text)
        quant = convertValue(splitElem.find('{http://www.gnucash.org/XML/split}quantity').text)
        if self.value != quant:
            raise Exception('ambiguous split value', splitElem, self.value, quant)
        self.account = gnucashId(splitElem, '{http://www.gnucash.org/XML/split}account')
        self.description = xmlText(splitElem, '{http://www.gnucash.org/XML/split}memo')

class GnucashFile (object):
    def __init__ (self, gnucashFile):
        with gzip.open(gnucashFile, 'rb') as f:
            d = etree.parse(f)
        aa = [ Account(a) for a in d.findall('.//{http://www.gnucash.org/XML/gnc}account') ]
        self.accounts = dict([ (a.id, a) for a in aa ])
        # risolvo i riferimenti
        self.root = None
        self.transactions = [ Transaction(t) for t in d.findall('.//{http://www.gnucash.org/XML/gnc}transaction') ]
        for a in self.accounts.values():
            if a.parent is None:
                if self.root is None:
                    self.root = a
                else:
                    raise Exception('multiple roots', self.root.id, a.id)
                continue
            p = self.accounts.get(a.parent, None)
            if p is None:
                raise Exception('account not found', a.parent)
            a.parentAccount = p
            p.children.append(a)
        for t in self.transactions:
            for s in t.splits:
                p = self.accounts.get(s.account, None)
                if p is None:
                    raise Exception('account not found', s.account)
                s.account = p
                s.account.saldo += s.value

def printAccountTree (a, indent=0):
    print('%s%s%s' % (' ' * indent, a.name, ':' if a.children else ''))
    for c in a.children:
        printAccountTree(c, indent + 1)

class importGnucash (object):
    def __init__ (self, g, conn, log):
        self.g = g
        self.conn = conn
        self.cursor = conn.cursor()
        self.log = log
        try:
            self.checkAccounts()
            self.checkTransactions()
            self.conn.commit()
        except:
            etype, evalue, tb = sys.exc_info()
            self.log('unexpected exception: error=%s/%s\n%s' % (etype, evalue, ''.join(traceback.format_tb(tb))))
            self.conn.rollback()
        finally:
            self.cursor.close()

    def checkAccounts (self):
        self.log('Checking accounts...')
        for a in self.g.accounts.values():
            self.cursor.execute('SELECT id, gc_name, gc_desc, gc_type, gc_parent FROM account WHERE gc_id=%s', [ a.id ])
            if self.cursor.rowcount == 1:
                dbId, gcName, gcDesc, gcType, gcParent = self.cursor.fetchone()
                a.dbId = dbId
                if a.name != gcName or a.description != gcDesc or a.type != gcType or a.parent != gcParent:
                    self.log('Account changed: name=%s, gc_id=%s, id=%s\nPreviuous infos: name=%s, desc=%s, type=%s, parent=%s\nGc infos: desc=%s, type=%s, parent=%s' % (
                             a.name, a.id, a.dbId,
                             gcName, gcDesc, gcType, gcParent,
                             a.description, a.type, a.parent
                             ))
                    # TODO: chiedi conferma
                    self.cursor.execute('UPDATE account SET gc_name=%s, gc_desc=%s, gc_type=%s, gc_parent=%s WHERE id=%s',
                                        [ dbText(a.name),
                                          dbText(a.description),
                                          a.type,
                                          a.parent,
                                          a.dbId
                                          ])
                else:
                    #self.log('Account found unchanged: name=%s, gc_id=%s, id=%s' % (a.name, a.id, a.dbId))
                    pass
            else:
                #self.log('Account not found, it will be created: gc_id=%s' % a.id)
                self.cursor.execute('INSERT INTO account (gc_id, gc_name, gc_desc, gc_type, gc_parent) VALUES (%s, %s, %s, %s, %s)',
                                    [
                                     a.id,
                                     dbText(a.name),
                                     dbText(a.description),
                                     a.type,
                                     a.parent,
                                     ])
                a.dbId = self.cursor.lastrowid
                self.log('Created account: name=%s, gc_id=%s, id=%s' % (a.name, a.id, a.dbId))

    def checkTransactions (self):
        self.log('Checking transactions...')
        for t in self.g.transactions:
            self.checkTransaction(t)

    def checkTransaction (self, t):
        self.cursor.execute('SELECT id, description, transaction_date FROM transaction WHERE gc_id=%s AND modified_by_id IS NULL', [ t.id ])
        if self.cursor.rowcount == 1:
            dbId, description, transaction_date = self.cursor.fetchone()
            t.dbId = dbId

            self.cursor.execute('SELECT id, account_id, description, amount, gc_id FROM transaction_line WHERE transaction_id=%s', [ t.dbId ])
            dbSplits = list(self.cursor)
            if description != t.description or transaction_date != t.date or  not self.matchSplits(t, dbSplits):
                self.log('Transaction changed, rewriting: id=%s, gcId=%s' % (t.id, t.dbId))
                self.insertTransaction(t, t.dbId)
            else:
                #self.log('Transaction found, attributes unchanged')
                pass
        else:
            self.insertTransaction(t, None)

    def matchSplits (self, t, dbSplits):
        '''Confronta gli splits in t (Transaction) con quelli su db
        (array di tuple 0:id, 1:account_id, 2:description, 3:amount, 4:gc_id)
        '''
        if len(t.splits) != len(dbSplits):
            return False
        dbIndex = dict([ (x[-1],x) for x in dbSplits ])
        for s in t.splits:
            dbs = dbIndex.get(s.id, None)
            if dbs is None:
                return False
            if (s.account.dbId != dbs[1] or
                s.description != dbs[2] or
                s.value != decimal.Decimal(dbs[3])):
                self.log('Transaction split changed: t=%s (%s), split=%s (%s)' % (t.dbId, t.id, dbs[0], s.id))
                # FIXME: scazzo a leggere le stringhe utf8 dal db
#                mi ritorna una stringa 
#>>> cur.execute('select description from transaction_line where id=9696')
#1
#>>> list(cur)
#[('uno per sÃ© uno per "mauro roberta renzo"',)]

                return False
            s.dbId = s.id
        return True

    def insertTransaction (self, t, oldTid):
        self.cursor.execute('INSERT INTO transaction (description, transaction_date, gc_id) VALUES (%s, %s, %s)',
                            [ dbText(t.description),
                              t.date,
                              t.id
                              ])
        t.dbId = self.cursor.lastrowid
        for s in t.splits:
            self.cursor.execute('INSERT INTO transaction_line (transaction_id, account_id, description, amount, gc_id) VALUES (%s, %s, %s, %s, %s)',
                            [t.dbId,
                             s.account.dbId,
                             dbText(s.description),
                             s.value,
                             s.id
                             ])
            s.dbId = self.cursor.lastrowid
        self.log('Created transaction: id=%s, dbId=%s, date=%s' % (s.id, s.dbId, t.date))
        if oldTid is not None:
            self.cursor.execute('UPDATE transaction SET modified_by_id=%s WHERE id=%s', [ t.dbId, oldTid ])

if __name__ == '__main__':
    opt.define('f', help='GnuCash data file')
    opt.define('host', default='localhost', help='MySQL database host')
    opt.define('port', default=3306, help='MySQL database port')
    opt.define('db', default='gassman', help='MySQL database name')
    opt.define('user', default='gassman', help='MySQL database user')
    opt.define('password', default='gassman', help='MySQL database user password')

    opt.parse_command_line()

    g = GnucashFile(opt.options.f)

    conn = pymysql.connect(host=opt.options.host, port=opt.options.port, user=opt.options.user, passwd=opt.options.password, db=opt.options.db, charset='utf8')

    importGnucash(g, conn, print)

    conn.close()
