#!/usr/bin/env python
'''
Created on 30/mar/2015

@author: makeroo
'''

import pymysql

import gassman_settings as settings

class AccountInfo:
    def __init__ (self, accountId, gcName):
        self.accountId = accountId
        self.gcName = gcName
        self.owners = dict()

    def addOwner (self, personId, firstName, lastName):
        self.owners[personId] = '%s %s' % (firstName, lastName)

    def calcGcName (self):
        return ', '.join(sorted(self.owners.values()))

def run (csa_id):
    connArgs = dict(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    passwd=settings.DB_PASSWORD,
                    db=settings.DB_NAME,
                    charset='utf8'
                    )
    conn = pymysql.connect(**connArgs)
    accounts = dict()
    with conn as cur:
        cur.execute('''
select a.id, a.gc_name, p.id, p.first_name, p.last_name
  from account a
  join account_person ap on ap.account_id = a.id
  join person p on ap.person_id = p.id

  where
    a.csa_id = %s and
    ap.to_date is null
  ;
''',
                    [ csa_id]
                    )
        for accountId, gcName, personId, firstName, lastName in cur:
            a = accounts.setdefault(accountId, AccountInfo(accountId, gcName))
            a.addOwner(personId, firstName, lastName)
        for accountId, info in accounts.items():
            update = False
            cgcn = info.calcGcName()
            if info.gcName is None or len(info.gcName) == 0:
                update = True
                print('account without name: %s', info.accountId)
            elif info.gcName != cgcn:
                update = True
                print('account with incorrect name: %s=%s', info.accountId, info.gcName)
            else:
                pass
            if update:
                q = 'update account set gc_name=%s where id=%s'
                a = [ cgcn, info.accountId ]
                print('executing update: %s %s', q, a)
                cur.execute(q, a)

if __name__ == '__main__':
    run(1)
