#!/usr/local/bin/python3
# encoding=utf-8


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

    def help_EOF (self): print('Just type Ctrl-D to quit panels manager.')
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
    def do_list_csa (self, line):
        with self.conn as cur:
            cur.execute('select id, name, description from csa order by id')
            for csa in list(cur):
                print('%3d %s%s' % (csa[0], csa[1], ': %s' % csa[2] if csa[2] else ''))

    def help_list_currency (self): print('List all currencies')
    def do_list_currency (self, line):
        with self.conn as cur:
            cur.execute('select id, symbol, iso_4217 from currency order by id')
            for csa in list(cur):
                print('%3d %s (%s)' % (csa[0], csa[1], csa[2]))

    def help_select_csa (self): print('Select CSA. Usage: select_csa <CSAID>')
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

    def help_create_person (self): print('Create a person profile with account. Usage: create_person <FIRSTNAME> <LASTNAME>')
    def do_create_person (self, line):
        if not self.selectedCsa:
            print('No CSA selected')
            return
        nn = line.split()
        fn, mn, ln = None, None, None
        if len(nn) == 2:
            fn = nn[0]
            ln = nn[1]
            q = 'insert into person (first_name, last_name) values (%s, %s)'
            args = [ fn, ln ]
        elif len(nn) > 2:
            fn = nn[0]
            ln = nn[-1]
            mn = line.strip()[len(fn):-len(ln)].strip()
            q = 'insert into person (first_name, middle_name, last_name) values (%s, %s, %s)'
            args = [ fn, mn, ln ]
        else:
            print('Missing name')
            return
        with self.conn as cur:
            cur.execute(q, args)
            pid = cur.lastrowid
            print('created person', pid)
            cur.execute('insert into permission_grant (csa_id, person_id, perm_id) values (%s, %s, %s)', [ self.selectedCsa, pid, sql.P_membership ])
            cur.execute('select id, symbol from currency')
            for r in list(cur):
                cid = r[0]
                csym = r[1]
                cur.execute('insert into account (state, gc_type, csa_id, currency_id) values (%s, %s, %s, %s)', [ sql.As_Open, sql.At_Asset, self.selectedCsa, cid ])
                aid = cur.lastrowid
                print('created account', aid, 'for currency', csym)
                cur.execute('insert into account_person (from_date, person_id, account_id) values (now(), %s, %s)', [ pid, aid ])

    def help_find_person (self): print('')
    def do_find_person (self, line):
        p = line.strip()
        with self.conn as cur:
            cur.execute('''
select p.id, p.first_name, p.middle_name, p.last_name, c.kind, c.address from person p
 join person_contact pc on pc.person_id=p.id
 join contact_address c on pc.address_id=c.id
 join account_person ap on ap.person_id=p.id
 join account
 where p.first_name like %s or
  p.middle_name like %s or
  p.last_name like %s or
  c.address like %s
  order by p.id''', [ p, p, p, p ])
            for r in list(cur):
                print(r)

    # TODO: creare una persona senza conto, ma agganciata al conto di un altro
    def help_add_person (self): print('')
    def do_add_person (self, line):
        pass
#    def help_select_csa (self): print('Select CSA. Usage: select_csa <CSAID>')
#    def do_select_csa (self, line):
#        with self.conn as cur:
#            k = line.strip()
#            try:
#                cur.execute('select name from csa where id=%s', [ k ])
#                self.selectedCsaName = cur.fetchone()[0]
#                self.selectedCsa = k
#                self.setPrompt()
#            except:
#                print('Unknown csa')

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