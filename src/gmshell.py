#!/usr/bin/env python3

'''
Created on 30/mag/2014

@author: makeroo
'''

import os
import cmd
import traceback
import sys
import datetime

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

    def help_create_person (self): print('Create a person profile with account. Usage: create_person <FIRSTNAME> <LASTNAME>')
    @catchall
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
            cur.execute('update person set rss_feed_id=%s where id=%s',
                        [
                         rss_feed_id(pid),
                         pid
                         ])
            print('created person', pid)
            cur.execute('insert into permission_grant (csa_id, person_id, perm_id) values (%s, %s, %s)', [ self.selectedCsa, pid, sql.P_membership ])
            cur.execute('select id, symbol from currency')
            for r in list(cur):
                cid = r[0]
                csym = r[1]
                cur.execute('insert into account (state, gc_type, csa_id, currency_id) values (%s, %s, %s, %s)', [ sql.As_Open, sql.At_Asset, self.selectedCsa, cid ])
                aid = cur.lastrowid
                print('created account', aid, 'for currency', csym)
                cur.execute('insert into account_person (from_date, person_id, account_id) values (utc_timestamp(), %s, %s)', [ pid, aid ])

    def help_find_person (self): print('Look for people by name, contacts, etc. Usage: find_person <LIKETEXT>')
    @catchall
    def do_find_person (self, line):
        p = line.strip()
        with self.conn as cur:
            cur.execute('''
select distinct p.id, p.first_name, p.middle_name, p.last_name, c.kind, c.address from person p
 left join person_contact pc on pc.person_id=p.id
 left join contact_address c on pc.address_id=c.id
 left join account_person ap on ap.person_id=p.id
 left join account a on ap.account_id=a.id
 where p.first_name like %s or
  p.middle_name like %s or
  p.last_name like %s or
  c.address like %s or
  a.gc_name like %s
  order by p.id''', [ p, p, p, p, p ])
            for r in list(cur):
                print(r)

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

    def help_add_contact (self): print('Add contact to existing person. Usage: <PID> <ADDRESS> <KIND> <TYPE>')
    @catchall
    def do_add_contact(self, line):
        pid, address, kind, ctype = line.split()
        kk = dict([ (v, k[3:]) for k, v in vars(sql).items() if k.startswith('Ck_')])
        if kind not in kk:
            print('illegal kind, use one of:', kk)
            return
        with self.conn as cur:
            cur.execute('insert into contact_address (address,kind,contact_type) values (%s, %s, %s)', [ address, kind, ctype ])
            aid = cur.lastrowid
            cur.execute('insert into person_contact (person_id, address_id, priority) select p.id, %s, 0 from person p where p.id=%s', [ aid, pid ])

    def help_find_account (self): print('Look for account by old GnuCash account name. Usage: find_account <LIKETEXT>')
    @catchall
    def do_find_account (self, line):
        p = line.strip()
        with self.conn as cur:
            cur.execute('''
select a.id, a.gc_name from account a
 where a.gc_name like %s
 order by a.id''', [ p ])
            for r in list(cur):
                print(r)

    # TODO: creare una persona senza conto, ma agganciata al conto di un altro
    def help_add_person (self): print('')
    @catchall
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

    def help_charge_kitty_amount (self): print('Charge per account defined kitty amount to each open account. Usage: charge_kitty_amount <userid> <transaction description>')
    @catchall
    def do_charge_kitty_amount (self, line):
        if not self.selectedCsa:
            print('No CSA selected')
            return
        x = line.index(' ')
        uid = int(line[:x])
        tDesc = line[x:].strip() or "Quota cassa comune"
        with self.conn as cur:
            now = datetime.datetime.utcnow()
            cur.execute('select id, currency_id from account where csa_id = %s and gc_type = %s', [ self.selectedCsa, sql.At_Kitty ])
            kittyId, currencyId = cur.fetchone()
            cur.execute(*sql.insert_transaction(tDesc,
                                                now,
                                                sql.Tt_CashExchange,
                                                currencyId,
                                                self.selectedCsa
                                                )
                        )
            tid = cur.lastrowid
            cur.execute('select a.id, - a.annual_kitty_amount from account a where a.csa_id=%s and a.currency_id=%s and a.annual_kitty_amount > 0', [ self.selectedCsa, currencyId ])
            for accId, amount in cur:
                cur.execute(*sql.insert_transaction_line(tid, '', amount, accId))
            cur.execute(*sql.complete_cashexchange(tid, kittyId))
            cur.execute(*sql.log_transaction(tid, uid, sql.Tl_Added, sql.Tn_kitty_deposit, now))

    @catchall
    def do_merge_people (self, line):
        # select * from person where first_name ='livia';
        # select * from person_contact where person_id in (398, 452);
        # select * from permission_grant where person_id in (398, 452);
        # select * from account_person where person_id in (398, 452);
        # update permission_grant set person_id = 452 where person_id = 398;
        # update account_person set person_id = 452 where person_id = 398;
        # delete from person where id=398;
        pass

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
