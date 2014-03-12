'''
Created on 03/mar/2014

@author: makeroo
'''

P_membership = 1
P_canCheckAccounts = 2
P_canAssignAccounts = 3

def account_movements (accountDbId, fromLine, toLine):
    return 'SELECT t.description, t.transaction_date, l.description, l.amount FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id WHERE t.modified_by_id IS NULL AND l.account_id=%s ORDER BY t.transaction_date DESC LIMIT %s OFFSET %s', [
        accountDbId,
        toLine - fromLine + 1,
        fromLine
        ]

def account_amount (accountDbId):
    return 'SELECT SUM(l.amount) FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id WHERE t.modified_by_id IS NULL AND l.account_id=%s', [ accountDbId ]

def check_user (userId, authenticator):
    return 'SELECT p.id, p.first_name, p.middle_name, p.last_name, p.current_account_id FROM contact_address c JOIN person_contact pc ON c.id=pc.address_id JOIN person p ON p.id=pc.person_id WHERE c.kind=%s AND c.contact_type=%s AND c.address=%s', [ 'I', authenticator, userId ]

def create_contact (addr, kind, contactType):
    return 'INSERT INTO contact_address (address, kind, contact_type) VALUES (%s,%s,%s)', [ addr, kind, contactType ]

def create_person (first, middle, last):
    return 'INSERT INTO person (first_name, middle_name, last_name) VALUES (%s,%s,%s)', [first, middle, last]

def assign_contact (contact, person):
    return 'INSERT INTO person_contact (person_id, address_id) VALUES (%s, %s)', [ person, contact ]

def find_person (pid):
    return 'SELECT id, first_name, middle_name, last_name, current_account_id FROM person WHERE id=%s', [ pid ]

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

def checkConn ():
    return 'SELECT 1 FROM DUAL'
