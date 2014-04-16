'''
Created on 03/mar/2014

@author: makeroo
'''

P_membership = 1
P_canCheckAccounts = 2
P_canAssignAccounts = 3
P_canEnterDeposit = 4
P_canEnterPayments = 5
P_canManageTransactions = 6

Tt_Generic = 'G'
Tt_Deposit = 'D'
Tt_Payment = 'P'
Tt_Trashed = 'T'
Tt_Unfinished = 'U'
Tt_Error = 'E'

Ck_Telephone = 'T'
Ck_Mobile = 'M'
Ck_Email = 'E'
Ck_Fax = 'F'
Ck_Id = 'I'
Ck_Nickname = 'N'

As_Open = 'O'
As_Closing = 'C'
As_closeD = 'D'
As_Fusion_pending = 'F'

Tl_Added = 'A'
Tl_Deleted = 'D'
Tl_Modified = 'M'
Tl_Error = 'E'

def account_owners (accountId):
    return 'SELECT p.first_name, p.middle_name, p.last_name FROM person p JOIN account_person ap ON ap.person_id=p.id WHERE ap.account_id=%s AND ap.to_date IS NULL', [ accountId ]

def account_movements (accountDbId, fromLine, toLine):
    return 'SELECT t.description, t.transaction_date, l.description, l.amount, t.id, c.symbol FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id JOIN currency c ON c.id=t.currency_id WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND l.account_id=%s ORDER BY t.transaction_date DESC LIMIT %s OFFSET %s', [
        Tt_Unfinished, Tt_Error,
        accountDbId,
        toLine - fromLine + 1,
        fromLine
        ]

def account_amount (accountDbId):
    return 'SELECT SUM(l.amount), c.symbol FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id JOIN account a on l.account_id=a.id JOIN currency c ON c.id=a.currency_id WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND l.account_id=%s', [ Tt_Unfinished, Tt_Error, accountDbId ]
    #return 'SELECT SUM(l.amount) FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id WHERE t.modified_by_id IS NULL AND l.account_id=%s', [ accountDbId ]

def accounts_index (fromLine, toLine):
    return '''SELECT p.id, p.first_name, p.middle_name, p.last_name, a.id, sum(l.amount), c.symbol\
 FROM person p\
 JOIN account_person ap ON ap.person_id=p.id\
 JOIN account a ON a.id=ap.account_id\
 JOIN transaction_line l ON l.account_id=a.id\
 JOIN transaction t ON t.id=l.transaction_id\
 JOIN currency c ON c.id=a.currency_id\
 WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) \
 GROUP BY p.id, a.id\
 ORDER BY p.first_name, p.last_name\
 LIMIT %s OFFSET %s''', [
      Tt_Unfinished, Tt_Error,
      toLine - fromLine + 1,
      fromLine
      ]

def check_user (userId, authenticator):
    return 'SELECT p.id, p.first_name, p.middle_name, p.last_name, p.rss_feed_id FROM contact_address c JOIN person_contact pc ON c.id=pc.address_id JOIN person p ON p.id=pc.person_id WHERE c.kind=%s AND c.contact_type=%s AND c.address=%s', [ 'I', authenticator, userId ]

def create_contact (addr, kind, contactType):
    return 'INSERT INTO contact_address (address, kind, contact_type) VALUES (%s,%s,%s)', [ addr, kind, contactType ]

def create_person (first, middle, last):
    return 'INSERT INTO person (first_name, middle_name, last_name) VALUES (%s,%s,%s)', [ first, middle, last ]

def assign_rss_feed_id (personId, rss_feed_id):
    return 'UPDATE person SET rss_feed_id=%s WHERE id=%s', [ rss_feed_id, personId ]

def assign_contact (contact, person):
    return 'INSERT INTO person_contact (person_id, address_id) VALUES (%s, %s)', [ person, contact ]

def find_person (pid):
    return 'SELECT id, first_name, middle_name, last_name, rss_feed_id FROM person WHERE id=%s', [ pid ]

#def find_current_account (pid):
#    return 'SELECT current_account_id FROM person WHERE id=%s', [ pid ]

def has_accounts (pid):
    return 'SELECT count(*) FROM account_person WHERE person_id=%s AND to_date IS NULL', [ pid ]

def has_account (pid, accId):
    return 'SELECT count(*) FROM account_person WHERE person_id=%s AND account_id=%s AND to_date IS NULL', [ pid, accId ]

def find_visible_permissions (personId):
    return 'SELECT id, name, description, visibility FROM permission p WHERE visibility <= (SELECT MAX(p.visibility) FROM permission p JOIN permission_grant g ON p.id=g.perm_id JOIN person u ON g.person_id=u.id WHERE u.id=%s) ORDER BY visibility, ord, name', [ personId ]

def find_user_permissions (personId):
    return 'SELECT g.perm_id FROM person u JOIN permission_grant g ON g.person_id=u.id WHERE u.id=%s', [ personId ]
    #return 'SELECT p.id FROM person u JOIN permission_grant g ON g.person_id=u.id JOIN permission p ON g.perm_id=p.id WHERE u.id=%s', [ personId ]

def find_user_csa (personId):
    return 'SELECT c.id, c.name FROM csa c JOIN permission_grant g ON c.id=g.csa_id WHERE g.person_id=%s AND g.perm_id=%s', [ personId, P_membership ]

def find_user_accounts (personId):
    return 'SELECT a.csa_id, a.id, ap.from_date, ap.to_date FROM account_person ap JOIN account a ON ap.account_id = a.id WHERE ap.person_id = %s ORDER BY a.csa_id, ap.from_date', [ personId ]

# TODO: si ripristina se si fa la pagina di associazione conto...
#def find_users_without_account ():
#    return 'SELECT id, first_name, middle_name, last_name FROM person WHERE current_account_id IS NULL'

def has_permission_by_account (perm, personId, accId):
    '''Uso accId solo per determinare la CSA, non verifico che personId abbia intestato accId, anzi in generale non è vero.
    Vedi il caso canCheckAccounts.
    '''
    return 'SELECT count(*) FROM permission_grant g JOIN account a ON a.csa_id=g.csa_id WHERE g.perm_id=%s AND g.person_id=%s AND a.id=%s', [ perm, personId, accId ]
#    return 'SELECT count(*) FROM permission_grant g JOIN account a ON a.csa_id=g.csa_id JOIN account_person ap ON ap.person_id=g.person_id WHERE g.perm_id=%s AND g.person_id=%s AND a.id=%s AND ap.to_date IS NULL', [ perm, personId, accId ]

def has_permission_by_csa (perm, personId, csaId):
    return 'SELECT count(*) FROM permission_grant WHERE perm_id=%s AND person_id=%s AND csa_id=%s', [ perm, personId, csaId ]

def has_permissions (perms, personId, csaId):
    return 'SELECT count(*) FROM permission_grant WHERE perm_id in (%s) AND person_id=%%s AND csa_id=%%s' % ', '.join(['%s'] * len(perms)), list(perms) + [ personId, csaId ]

def transaction_lines (tid):
    return 'SELECT id, account_id, description, amount FROM transaction_line WHERE transaction_id=%s ORDER BY id', [ tid ]

def transaction_people (tid):
    # qui non verifico che acount_person sia del csa giusto perché è implicito nella transazione
    return 'SELECT DISTINCT p.id, p.first_name, p.middle_name, p.last_name, l.account_id FROM transaction_line l JOIN account_person ap ON ap.account_id=l.account_id JOIN person p ON ap.person_id=p.id WHERE transaction_id=%s AND ap.to_date IS NULL', [ tid ]

def transaction_account_gc_names (tid):
    return 'SELECT DISTINCT a.id, a.gc_name, c.symbol FROM transaction_line l JOIN account a ON a.id=l.account_id JOIN currency c ON c.id=a.currency_id WHERE transaction_id=%s', [ tid ]

def rss_feed (rssId):
    return 'SELECT t.description, t.transaction_date, l.amount, l.id, c.symbol FROM transaction_line l JOIN transaction t ON t.id=l.transaction_id JOIN account_person ap ON ap.account_id=l.account_id JOIN account a ON l.account_id=a.id JOIN person p ON p.id=ap.person_id JOIN currency c ON c.id=a.currency_id WHERE p.rss_feed_id=%s AND ap.to_date IS NULL AND t.cc_type NOT IN (%s, %s) ORDER BY t.transaction_date DESC LIMIT 8', [ rssId, Tt_Unfinished, Tt_Error ]

def rss_user (rssId):
    return 'SELECT first_name, middle_name, last_name FROM person WHERE rss_feed_id=%s', [ rssId ]

def rss_id (personId):
    return 'SELECT rss_feed_id FROM person WHERE id=%s', [ personId ]

def csa_amount (csaId):
    return 'SELECT SUM(l.amount), c.symbol FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id JOIN account a ON l.account_id=a.id JOIN currency c ON c.id=a.currency_id WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND a.gc_type=%s AND a.csa_id=%s GROUP BY c.symbol', [ Tt_Unfinished, Tt_Error, 'ASSET', csaId ]

def account_names (csaId):
    '''Tutti i nomi di conti di una comunità escluso gli Scomparsi.
    FIXME: prima o poi scompariranno le colonne gc!
    '''
    return 'SELECT a.gc_name, a.id, c.id, c.symbol FROM account a JOIN currency c ON a.currency_id=c.id WHERE a.csa_id = %s AND a.gc_parent = %s AND a.gc_id <> %s', [ csaId, 'acf998ffe1edbcd44bc30850813650ac', '5ba64cec222104efb491ceafd6dd1812' ]

def account_people (csaId):
    return 'SELECT p.id, p.first_name, p.middle_name, p.last_name, a.id FROM person p JOIN account_person ap ON p.id=ap.person_id JOIN account a ON ap.account_id=a.id WHERE a.csa_id=%s AND ap.to_date IS NULL', [ csaId ]

def account_people_addresses (csaId):
    return 'SELECT c.address, p.id, a.id FROM person p JOIN account_person ap ON ap.person_id=p.id JOIN account a ON ap.account_id=a.id JOIN person_contact pc ON p.id=pc.person_id JOIN contact_address c ON pc.address_id=c.id WHERE a.csa_id=%s AND c.kind IN (%s, %s) AND ap.to_date IS NULL', [ csaId, Ck_Email, Ck_Nickname ]

def insert_transaction (desc, tDate, ccType, currencyId):
    return 'INSERT INTO transaction (description, transaction_date, cc_type, currency_id) SELECT %s, %s, %s, id FROM currency WHERE id=%s', [ desc, tDate, ccType, currencyId ]

def insert_transaction_line (tid, desc, amount, accId):
    return 'INSERT INTO transaction_line (transaction_id, account_id, description, amount) SELECT %s, a.id, %s, %s FROM account a WHERE a.id = %s', [ tid, desc, amount, accId ]

def check_transaction_coherency (tid):
    return 'SELECT DISTINCT a.currency_id, a.csa_id FROM transaction_line l JOIN account a ON a.id=l.account_id WHERE l.transaction_id = %s', [ tid ]

def complete_deposit (tid, csaId):
    return 'INSERT INTO transaction_line (transaction_id, account_id, amount) SELECT l.transaction_id, c.income_id, - SUM(l.amount) FROM csa c, transaction_line l WHERE c.id=%s AND l.transaction_id=%s', [ csaId, tid ]

def finalize_transaction (tid, ttype):
    return 'UPDATE transaction SET cc_type=%s WHERE id=%s', [ ttype, tid ]

def transaction_edit (tid):
    return 'SELECT t.description, t.transaction_date, t.cc_type, c.id, c.symbol, t.modified_by_id FROM transaction t JOIN currency c ON c.id=t.currency_id WHERE t.id=%s', [ tid ];

def log_transaction (tid, opId, logType, logDesc, tDate):
    return 'INSERT INTO transaction_log (log_date, operator_id, op_type, transaction_id, notes) VALUES (%s, %s, %s, %s, %s)', [ tDate, opId, logType, tid, logDesc ] 

def log_transaction_check_operator (personId, transId):
    return 'SELECT COUNT(*) FROM transaction_log WHERE transaction_id=%s AND operator_id=%s', [ transId, personId ]

def transaction_previuos (transId):
    return 'SELECT id FROM transaction WHERE modified_by_id = %s', [ transId ]

def transaction_type (transId):
    return 'SELECT cc_type, modified_by_id FROM transaction WHERE id = %s', [ transId ]

def update_transaction (oldTid, newTid):
    return 'UPDATE transaction SET modified_by_id = %s WHERE id = %s', [ newTid, oldTid ]

#select l.log_date, l.op_type, t.id, t.description, t.transaction_date, t.modified_by_id, p.id, p.first_name, p.middle_name, p.last_name  from transaction_log l join transaction t on t.id=l.transaction_id join person p on l.operator_id= p.id where l.op_type in ('A', 'M', 'D') order by l.log_date desc limit 25 offset 1;

def checkConn ():
    return 'SELECT 1'
