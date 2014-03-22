'''
Created on 03/mar/2014

@author: makeroo
'''

P_membership = 1
P_canCheckAccounts = 2
P_canAssignAccounts = 3

def account_owners (accountId):
    return 'SELECT first_name, middle_name, last_name FROM person WHERE current_account_id=%s', [ accountId ]

def account_movements (accountDbId, fromLine, toLine):
    return 'SELECT t.description, t.transaction_date, l.description, l.amount, t.id FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id WHERE t.modified_by_id IS NULL AND l.account_id=%s ORDER BY t.transaction_date DESC LIMIT %s OFFSET %s', [
        accountDbId,
        toLine - fromLine + 1,
        fromLine
        ]

def account_amount (accountDbId):
    return 'SELECT SUM(l.amount) FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id WHERE t.modified_by_id IS NULL AND l.account_id=%s', [ accountDbId ]

def accounts_index (fromLine, toLine):
    return '''SELECT p.id, p.first_name, p.middle_name, p.last_name, a.id, sum(l.amount)\
 FROM person p\
 JOIN account a ON a.id=p.current_account_id\
 JOIN transaction_line l ON l.account_id=a.id\
 JOIN transaction t ON t.id=l.transaction_id\
 WHERE t.modified_by_id IS NULL\
 GROUP BY p.id, a.id\
 LIMIT %s OFFSET %s
''', [
      toLine - fromLine + 1,
      fromLine
      ]

def check_user (userId, authenticator):
    return 'SELECT p.id, p.first_name, p.middle_name, p.last_name, p.current_account_id FROM contact_address c JOIN person_contact pc ON c.id=pc.address_id JOIN person p ON p.id=pc.person_id WHERE c.kind=%s AND c.contact_type=%s AND c.address=%s', [ 'I', authenticator, userId ]

def create_contact (addr, kind, contactType):
    return 'INSERT INTO contact_address (address, kind, contact_type) VALUES (%s,%s,%s)', [ addr, kind, contactType ]

def create_person (first, middle, last):
    return 'INSERT INTO person (first_name, middle_name, last_name) VALUES (%s,%s,%s)', [first, middle, last]

def assign_contact (contact, person):
    return 'INSERT INTO person_contact (person_id, address_id) VALUES (%s, %s)', [ person, contact ]

def find_person (pid):
    return 'SELECT id, first_name, middle_name, last_name, current_account_id, rss_feed_id FROM person WHERE id=%s', [ pid ]

def find_current_account (pid):
    return 'SELECT current_account_id FROM person WHERE id=%s', [ pid ]

def find_visible_permissions (personId):
    return 'SELECT id, name, description, visibility FROM permission p WHERE visibility <= (SELECT MAX(p.visibility) FROM permission p JOIN permission_grant g ON p.id=g.perm_id JOIN person u ON g.person_id=u.id WHERE u.id=%s) ORDER BY visibility, ord, name', [ personId ]

def find_user_permissions (personId):
    return 'SELECT p.id FROM person u JOIN permission_grant g ON g.person_id=u.id JOIN permission p ON g.perm_id=p.id WHERE u.id=%s', [ personId]

def find_user_csa (personId):
    return 'SELECT c.id, c.name FROM csa c JOIN permission_grant g ON c.id=g.csa_id WHERE g.person_id=%s AND g.perm_id=%s', [ P_membership, personId ]

def find_users_without_account ():
    return 'SELECT id, first_name, middle_name, last_name FROM person WHERE current_account_id IS NULL'

def has_permission (perm, personId):
    return 'SELECT count(*) FROM permission_grant WHERE perm_id=%s AND person_id=%s', [ perm, personId ]

def transaction_lines (tid):
    return 'SELECT id, account_id, description, amount FROM transaction_line WHERE transaction_id=%s ORDER BY id', [ tid ]

def transaction_people (tid):
    return 'SELECT DISTINCT p.id, p.first_name, p.middle_name, p.last_name, p.current_account_id FROM transaction_line l JOIN person p ON p.current_account_id=l.account_id WHERE transaction_id=%s', [ tid ]

def transaction_account_gc_names (tid):
    return 'SELECT DISTINCT a.id, a.gc_name FROM transaction_line l JOIN account a ON a.id=l.account_id WHERE transaction_id=%s', [ tid ]

def rss_feed (rssId):
    return 'SELECT t.description, t.transaction_date, l.amount, l.id FROM transaction_line l JOIN transaction t ON t.id=l.transaction_id JOIN account a ON l.account_id=a.id JOIN person p ON p.current_account_id=a.id WHERE p.rss_feed_id=%s ORDER BY t.transaction_date DESC LIMIT 8', [ rssId ]

def rss_user (rssId):
    return 'SELECT first_name, middle_name, last_name FROM person WHERE rss_feed_id=%s', [ rssId ]

def rss_id (personId):
    return 'SELECT rss_feed_id FROM person WHERE id=%s', [ personId ]

# FIXME: questa assume un solo csa!
# FIXME: correggere il 4.5 in gnucash!
def csa_amount ():
    return 'SELECT 4.5+SUM(l.amount) FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id JOIN account a ON l.account_id=a.id WHERE t.modified_by_id IS NULL AND a.gc_type=%s', [ 'ASSET' ]

def checkConn ():
    return 'SELECT 1'
