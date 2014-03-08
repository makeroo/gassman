'''
Created on 03/mar/2014

@author: makeroo
'''

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
    return 'SELECT id, first_name, middle_name, last_name, current_account_id FROM PERSON WHERE id=%s', [ pid ]
