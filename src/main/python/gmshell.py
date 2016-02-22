#!/usr/bin/env python3

'''
Created on 30/mag/2014

@author: makeroo
'''

import os
import cmd
import traceback
import sys

import pymysql

import gassman_settings as settings
import sql

last_error = None

from gassman import rss_feed_id

def catchall (func):
    def _func (*args):
        global last_error
        try:
            func(*args)
            last_error = None
        except Exception as e:
            print("Illegal command. Error: %s" % e)
            last_error = traceback.format_exc()
        except:
            print("Illegal command. %s" % traceback.format_exc())
    return _func

class GMShell (cmd.Cmd):
    def __init__ (self, conn):
        super(GMShell, self).__init__()
        self.prompt = '> '
        self.history_file = os.path.expanduser('~/.gassman.history')
        self.conn = conn
        self.selectedCsa = None
        self.selectedCsaName = None
        self.selectedCurrency = None
        self.selectedCurrencyName = None
        self.setPrompt()

    def setPrompt (self):
        if self.selectedCsa is None:
            if self.selectedCurrency is None:
                self.prompt = '> '
            else:
                self.prompt = '%s> ' % self.selectedCurrencyName
        elif self.selectedCurrency is None:
            self.prompt = '%s> ' % self.selectedCsaName
        else:
            self.prompt = '%s/%s> ' % (self.selectedCsaName, self.selectedCurrencyName)

    def help_help (self):
        print('Type help <cmd> to read <cmd> documentation.')

    def help_EOF (self): print('Just type Ctrl-D to quit.')
    def do_EOF (self, line):
        return True

    def preloop (self):
        try:
            import readline
            readline.read_history_file(self.history_file)
        except (ImportError, IOError):
            pass

    def postloop (self):
        try:
            import readline
            readline.write_history_file(self.history_file)
        except ImportError:
            pass
        print

    def help_last_error (self): print("Print last exception stack trace")
    def do_last_error (self, line):
        if last_error:
            print(last_error)

    def help_list_csa (self): print('List all CSA')
    @catchall
    def do_list_csa (self, line):
        with self.conn as cur:
            cur.execute('select id, name, description from csa order by id')
            for csa in list(cur):
                print('%3d %s%s' % (csa[0], csa[1], ': %s' % csa[2] if csa[2] else ''))

    def help_list_currency (self): print('List all currencies')
    @catchall
    def do_list_currency (self, line):
        with self.conn as cur:
            cur.execute('select id, symbol, iso_4217 from currency order by id')
            for csa in list(cur):
                print('%3d %s (%s)' % (csa[0], csa[1], csa[2]))

    def help_select_csa (self): print('Select CSA. Usage: select_csa <CSAID>')
    @catchall
    def do_select_csa (self, line):
        with self.conn as cur:
            k = line.strip()
            try:
                cur.execute('select name from csa where id=%s', [ k ])
                self.selectedCsaName = cur.fetchone()[0]
                self.selectedCsa = k
                self.setPrompt()
            except:
                print('Unknown csa')

    def help_show_person (self): print('Show full profile info. Usage: show_person <PID>')
    @catchall
    def do_show_person (self, line):
        pid = line.strip()
        with self.conn as cur:
            cur.execute('select * from person where id=%s', [ pid ])
            p = cur.fetchone()
            if p is None:
                print('not found')
                return
            for f, v in zip(cur.description, p):
                print('%s: %s' % (f[0], v))
            print()
            cur.execute('select c.* from person_contact pc join contact_address c on pc.address_id=c.id where pc.person_id=%s', [ pid ])
            for r in list(cur):
                print(', '.join([ '%s:%s' % (f[0], v) for f, v in zip(cur.description, r) ]))
            print()
            cur.execute('select ap.*, a.* from account_person ap join account a on ap.account_id=a.id where ap.person_id=%s', [ pid ])
            for r in list(cur):
                print(', '.join([ '%s:%s' % (f[0], v) for f, v in zip(cur.description, r) ]))
            print()
            cur.execute('select g.csa_id, p.name as perm from permission_grant g join permission p on g.perm_id=g.id where g.person_id=%s', [ pid ])
            for r in list(cur):
                print(' '.join([ '%s: %s' % (f[0], v) for f, v in zip(cur.description, r) ]))
            print()

if __name__ == '__main__':
    try:
        conn = pymysql.connect(host=settings.DB_HOST,
                               port=settings.DB_PORT,
                               user=settings.DB_USER,
                               passwd=settings.DB_PASSWORD,
                               db=settings.DB_NAME,
                               charset='utf8')
        sh = GMShell(conn)
        sh.cmdloop('GASsMan shell')
    except:
        print('Error: unexpected exception')
        traceback.print_exc(file = sys.stderr)
        sys.exit(1)
