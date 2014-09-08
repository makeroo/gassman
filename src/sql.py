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
P_canEnterCashExchange = 7
P_canEnterWithdrawal = 8
P_canViewContacts = 9
P_canEditContacts = 10
P_canGrantPermissions = 11

Tt_Generic = 'g'
Tt_Deposit = 'd'
Tt_Payment = 'p'
Tt_Trashed = 't'
Tt_CashExchange = 'x'
Tt_Withdrawal = 'w'
Tt_Unfinished = 'u'
Tt_Error = 'e'

An_EveryMovement = 'E'
An_Dayly = 'D'
An_Weekly = 'W'
An_Never = 'N'

Ck_Telephone = 'T'
Ck_Mobile = 'M'
Ck_Email = 'E'
Ck_Fax = 'F'
Ck_Id = 'I'
Ck_Nickname = 'N'

Ckk = set([Ck_Telephone,
           Ck_Mobile,
           Ck_Email,
           Ck_Fax,
           Ck_Id,
           Ck_Nickname,
           ])

transactionPermissions = {
    Tt_Deposit: P_canEnterDeposit,
    Tt_Payment: P_canEnterPayments,
    Tt_CashExchange: P_canEnterCashExchange,
    Tt_Withdrawal: P_canEnterWithdrawal,
#    Tt_Generic: P_canCheckAccounts
    }

editableTransactionPermissions = set(transactionPermissions.values())

deletableTransactions = set([
    Tt_Generic,
    Tt_Deposit,
    Tt_Payment,
    Tt_CashExchange,
    Tt_Withdrawal,
    ])
editableTransactions = set([
    Tt_Generic,
    Tt_Deposit,
    Tt_Payment,
    Tt_CashExchange,
    Tt_Withdrawal,
    Tt_Trashed,
#    Tt_Unfinished,
    ])

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

At_Asset = 'ASSET' # kitty
At_Expense = 'EXPENSE' # spese
At_Income = 'INCOME' # versamenti

def account_owners (accountId):
    return 'SELECT p.first_name, p.middle_name, p.last_name, p.id FROM person p JOIN account_person ap ON ap.person_id=p.id WHERE ap.account_id=%s AND ap.to_date IS NULL', [ accountId ]

def account_description (accountId):
    return 'SELECT a.gc_name, c.name, c.id FROM account a JOIN csa c ON a.csa_id=c.id WHERE a.id=%s', [ accountId ]

def account_movements (accountDbId, fromLine, toLine):
    return (
'''SELECT t.description, t.transaction_date, l.description, l.amount, t.id, c.symbol, t.cc_type
 FROM transaction t
 JOIN transaction_line l ON l.transaction_id=t.id
 JOIN currency c ON c.id=t.currency_id
 WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND l.account_id=%s
 ORDER BY t.transaction_date DESC
 LIMIT %s OFFSET %s''', [
        Tt_Unfinished, Tt_Error,
        accountDbId,
        toLine - fromLine + 1,
        fromLine
        ]
            )

def account_amount (accountDbId):
    return 'SELECT SUM(l.amount), c.symbol FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id JOIN account a on l.account_id=a.id JOIN currency c ON c.id=a.currency_id WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND l.account_id=%s', [ Tt_Unfinished, Tt_Error, accountDbId ]
    #return 'SELECT SUM(l.amount) FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id WHERE t.modified_by_id IS NULL AND l.account_id=%s', [ accountDbId ]

accounts_index_order_by = [ 'p.first_name, p.last_name',
                           'ta',
                           'td desc',
                           ]

def accounts_index (csaId, q, o, fromLine, toLine):
    return '''SELECT p.id, p.first_name, p.middle_name, p.last_name, a.id, sum(l.amount) AS ta, c.symbol, MAX(t.transaction_date) AS td
 FROM person p
 JOIN permission_grant g ON g.person_id=p.id
 LEFT JOIN account_person ap ON ap.person_id=p.id
 JOIN account a on ap.account_id=a.id
 JOIN currency c ON a.currency_id=c.id
 LEFT JOIN transaction_line l ON l.account_id=a.id
 LEFT JOIN transaction t ON t.id=l.transaction_id

 WHERE
 g.csa_id=%s AND
 g.perm_id=%s AND
 ap.to_date IS NULL AND
 t.modified_by_id IS NULL AND
 (t.cc_type IS NULL OR t.cc_type NOT IN (%s, %s)) AND
 (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s)

 GROUP BY p.id, a.id
 ORDER BY ''' + o + '''
 LIMIT %s OFFSET %s
''', [ csaId,
       P_membership,
       Tt_Unfinished, Tt_Error,
       q, q, q,
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

#def transaction_account_gc_names (tid):
#    return 'SELECT DISTINCT a.id, a.gc_name, c.symbol FROM transaction_line l JOIN account a ON a.id=l.account_id JOIN currency c ON c.id=a.currency_id WHERE transaction_id=%s', [ tid ]

def rss_feed (rssId):
    return 'SELECT t.description, t.transaction_date, l.amount, l.id, c.symbol FROM transaction_line l JOIN transaction t ON t.id=l.transaction_id JOIN account_person ap ON ap.account_id=l.account_id JOIN account a ON l.account_id=a.id JOIN person p ON p.id=ap.person_id JOIN currency c ON c.id=a.currency_id WHERE p.rss_feed_id=%s AND ap.to_date IS NULL AND t.cc_type NOT IN (%s, %s) ORDER BY t.transaction_date DESC LIMIT 8', [ rssId, Tt_Unfinished, Tt_Error ]

def rss_user (rssId):
    return 'SELECT first_name, middle_name, last_name FROM person WHERE rss_feed_id=%s', [ rssId ]

def rss_id (personId):
    return 'SELECT rss_feed_id FROM person WHERE id=%s', [ personId ]

def csa_amount (csaId):
    return 'SELECT SUM(l.amount), c.symbol FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id JOIN account a ON l.account_id=a.id JOIN currency c ON c.id=a.currency_id WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND a.gc_type=%s AND a.csa_id=%s GROUP BY c.symbol', [ Tt_Unfinished, Tt_Error, At_Asset, csaId ]

def csa_account (csaId, accountType, currencyId):
    return 'SELECT a.id FROM account_csa ac JOIN account a ON ac.account_id=a.id WHERE ac.csa_id=%s AND a.gc_type=%s AND a.currency_id=%s', [ csaId, accountType, currencyId ]

def account_currency (accId, csaId, requiredCurr):
    return 'SELECT count(*) FROM account a WHERE a.id=%s AND a.csa_id=%s AND a.currency_id=%s', [ accId, csaId, requiredCurr ]

#def account_names (csaId):
#    '''Tutti i nomi di conti di una comunità escluso gli Scomparsi.
#    FIXMe: prima o poi scompariranno le colonne gc!
#    '''
#    return 'SELECT a.gc_name, a.id, c.id, c.symbol FROM account a JOIN currency c ON a.currency_id=c.id WHERE a.csa_id = %s AND a.gc_parent = %s AND a.gc_id <> %s', [ csaId, 'acf998ffe1edbcd44bc30850813650ac', '5ba64cec222104efb491ceafd6dd1812' ]
def account_currencies (csaId):
    '''Tutti i conti di un csa.
    '''
    return 'SELECT a.id, c.id, c.symbol FROM account a JOIN currency c ON a.currency_id=c.id WHERE a.csa_id = %s', [ csaId ]

def account_people (csaId):
    return 'SELECT p.id, p.first_name, p.middle_name, p.last_name, a.id FROM person p JOIN account_person ap ON p.id=ap.person_id JOIN account a ON ap.account_id=a.id WHERE a.csa_id=%s AND ap.to_date IS NULL', [ csaId ]

def account_people_addresses (csaId):
    return 'SELECT c.address, p.id, a.id FROM person p JOIN account_person ap ON ap.person_id=p.id JOIN account a ON ap.account_id=a.id JOIN person_contact pc ON p.id=pc.person_id JOIN contact_address c ON pc.address_id=c.id WHERE a.csa_id=%s AND c.kind IN (%s, %s) AND ap.to_date IS NULL', [ csaId, Ck_Email, Ck_Nickname ]

def account_kitty (csaId):
    return 'SELECT a.id FROM account_csa ac JOIN account a ON ac.account_id=a.id WHERE ac.csa_id=%s AND a.gc_type=%s', [ csaId, At_Asset ]

def account_email_for_notifications (accountIds):
    return '''
SELECT ap.account_id, p.id, p.first_name, p.middle_name, p.last_name, c.address
 FROM account_person ap
 JOIN person p ON ap.person_id=p.id
 JOIN person_contact pc ON p.id=pc.person_id
 JOIN contact_address c ON pc.address_id=c.id
 WHERE ap.to_date IS NULL AND
       ap.account_id IN (%s) AND
       c.kind=%%s AND
       p.account_notifications=%%s
 ORDER BY ap.account_id, pc.priority''' % ','.join([ '%s' ] * len(accountIds)), list(accountIds) + [ Ck_Email, An_EveryMovement ]

def account_total_for_notifications (accountIds):
    return '''
SELECT a.id, sum(l.amount), c.symbol
 FROM account a
 JOIN currency c ON a.currency_id=c.id
 JOIN transaction_line l ON l.account_id=a.id
 JOIN transaction t ON t.id=l.transaction_id

 WHERE
 t.modified_by_id IS NULL AND
 t.cc_type NOT IN (%%s, %%s) AND
 a.id IN (%s)

 GROUP BY a.id
''' % (','.join(['%s'] * len(accountIds))), [ Tt_Unfinished, Tt_Error ] + list(accountIds)

def expenses_accounts (csaId):
    return 'SELECT id, gc_name, currency_id FROM account where gc_type =%s AND csa_id=%s AND state=%s', [ At_Expense, csaId, As_Open]

def expenses_line_descriptions (csaId):
    return 'SELECT DISTINCT l.description FROM transaction_line l JOIN account a ON l.account_id=a.id WHERE a.gc_type=%s AND a.csa_id=%s AND l.description IS NOT NULL', [ At_Expense, csaId ]

def expenses_transaction_descriptions (csaId):
    return 'SELECT DISTINCT t.description FROM transaction_line l JOIN account a ON l.account_id=a.id JOIN transaction t ON l.transaction_id=t.id WHERE a.gc_type=%s AND a.csa_id=%s AND t.description IS NOT NULL', [ At_Expense, csaId ]

def insert_transaction (desc, tDate, ccType, currencyId, csaId):
    return 'INSERT INTO transaction (description, transaction_date, cc_type, currency_id, csa_id) SELECT %s, %s, %s, id, %s FROM currency WHERE id=%s', [ desc, tDate, ccType, csaId, currencyId ]

def insert_transaction_line (tid, desc, amount, accId):
    return 'INSERT INTO transaction_line (transaction_id, account_id, description, amount) SELECT %s, a.id, %s, %s FROM account a WHERE a.id = %s', [ tid, desc, amount, accId ]

def check_transaction_coherency (tid):
    return 'SELECT DISTINCT a.currency_id, a.csa_id FROM transaction_line l JOIN account a ON a.id=l.account_id WHERE l.transaction_id = %s', [ tid ]

def complete_deposit_or_withdrawal (tid, csaId, atype):
    return '''
INSERT INTO transaction_line (transaction_id, account_id, amount)
 SELECT t.id, ca.id, - SUM(l.amount)
  FROM account_csa ac
  JOIN account ca ON ac.account_id=ca.id,

  transaction_line l
  JOIN transaction t ON l.transaction_id=t.id

  WHERE ca.csa_id=%s AND ca.gc_type=%s AND ca.currency_id=t.currency_id AND t.id=%s''', [ csaId, atype, tid ]

def complete_cashexchange (tid, receiverId):
    return '''
INSERT INTO transaction_line (transaction_id, account_id, amount)
 SELECT t.id, %s, - SUM(l.amount)
  FROM transaction_line l
  JOIN transaction t ON l.transaction_id=t.id
   WHERE t.id=%s''', [ receiverId, tid ]

#def complete_withdrawal2 (tid, csaId, receiverId):
#    '''Qui in un colpo solo verifico l'esistenza e la coerenza (per csa e moneta) di chi ritira i soldi
#    e calcolo il totale del ritiro.
#    '''
#INSERT INTO transaction_line (transaction_id, account_id, amount)
#    return '''
# SELECT t.id, a.id, - SUM(l.amount)
#  FROM transaction_line l
#  JOIN transaction t ON l.transaction_id=t.id,
#  account a
#   WHERE t.id=%s AND a.id=%s AND a.csa_id=%s AND a.currency_id=t.currency_id''', [ tid, receiverId, csaId ]

def transaction_calc_last_line_amount (tid, tlineId):
    return 'SELECT - SUM(amount) FROM transaction_line WHERE transaction_id = %s AND id != %s', [ tid, tlineId ]

def transaction_fix_amount (tlineId, amount):
    return 'UPDATE transaction_line SET amount = %s WHERE id = %s', [ amount, tlineId ]

def finalize_transaction (tid, ttype):
    return 'UPDATE transaction SET cc_type=%s WHERE id=%s', [ ttype, tid ]

def transaction_edit (tid):
    return '''
SELECT t.description, t.transaction_date, t.cc_type, c.id, c.symbol, t.modified_by_id, t2.id
 FROM transaction t
 LEFT JOIN transaction t2 on t.id=t2.modified_by_id
 JOIN currency c ON c.id=t.currency_id
 WHERE t.id=%s''', [ tid ]

def log_transaction (tid, opId, logType, logDesc, tDate):
    return 'INSERT INTO transaction_log (log_date, operator_id, op_type, transaction_id, notes) VALUES (%s, %s, %s, %s, %s)', [ tDate, opId, logType, tid, logDesc ] 

def log_transaction_check_operator (personId, transId):
    return 'SELECT COUNT(*) FROM transaction_log WHERE transaction_id=%s AND operator_id=%s', [ transId, personId ]

def transaction_is_involved (transId, personId):
    return 'SELECT COUNT(*) FROM transaction_line l JOIN account a ON l.account_id=a.id JOIN account_person ap ON a.id=ap.account_id WHERE l.transaction_id=%s AND ap.person_id=%s', [ transId, personId ]

def transaction_previuos (transId):
    return 'SELECT id FROM transaction WHERE modified_by_id = %s', [ transId ]

def transaction_type (transId):
    return 'SELECT cc_type, modified_by_id FROM transaction WHERE id = %s', [ transId ]

def update_transaction (oldTid, newTid):
    return 'UPDATE transaction SET modified_by_id = %s WHERE id = %s', [ newTid, oldTid ]

transactions_editable_order_by = [ 'l.log_date DESC',
                           't.transaction_date DESC',
                           'p.first_name,p.last_name',
                           't.description'
                           ]

def transactions_all (csaId, q, o, fromLine, toLine):
    return '''SELECT l.id, l.log_date, l.op_type, t.id, t.description, t.transaction_date, t.modified_by_id, t.cc_type, p.id, p.first_name, p.middle_name, p.last_name
     FROM transaction_log l
     JOIN transaction t ON t.id=l.transaction_id
     JOIN person p ON l.operator_id= p.id

     WHERE t.csa_id=%s AND l.op_type IN (%s, %s, %s) AND
      (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s OR t.description LIKE %s)

     ORDER BY ''' + o + ''' LIMIT %s OFFSET %s''', [
            csaId,
            'A', 'M', 'D',
            q, q, q, q,
            toLine - fromLine + 1,
            fromLine
            ]

def transactions_by_editor (csaId, operator, q, o, fromLine, toLine):
    return '''SELECT l.id, l.log_date, l.op_type, t.id, t.description, t.transaction_date, t.modified_by_id, t.cc_type, p.id, p.first_name, p.middle_name, p.last_name
     FROM transaction_log l
     JOIN transaction t ON t.id=l.transaction_id
     JOIN person p ON l.operator_id= p.id

     WHERE t.csa_id=%s AND l.operator_id=%s AND l.op_type IN (%s, %s, %s) AND
      (t.description LIKE %s)

     ORDER BY ''' + o + ''' LIMIT %s OFFSET %s''', [
            csaId,
            operator.id,
            'A', 'M', 'D',
            q,
            toLine - fromLine + 1,
            fromLine
            ]

def people_index (csaId, q, o, fromLine, toLine):
    return '''
SELECT p.id, p.first_name, p.middle_name, p.last_name
 FROM person p
 JOIN permission_grant g ON p.id=g.person_id

 WHERE g.csa_id=%s AND g.perm_id=%s AND
 (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s)
 ORDER BY ''' + o + '''
 LIMIT %s OFFSET %s
 ''', [
       csaId,
       P_membership,
       q, q, q,
       toLine - fromLine + 1,
       fromLine
       ]
#def people_index (csaId, q, o, fromLine, toLine):
#    return '''
#SELECT p.id, p.first_name, p.middle_name, p.last_name, p.rss_feed_id, p.account_notifications,  a.id, a.first_line, a.second_line, a.zip_code, a.description, c.name, s.name, s.iso3
# FROM person p
# JOIN permission_grant g ON p.id=g.person_id
# LEFT JOIN street_address a ON p.address_id=a.id
# LEFT JOIN city c ON a.city_id=c.id
# LEFT JOIN state s ON c.state_id=s.id
#
# WHERE g.csa_id=%s AND g.perm_id=%s AND
# (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s)
# ORDER BY ''' + o + '''
# LIMIT %s OFFSET %s
# ''', [
#       csaId,
#       P_membership,
#       q, q, q,
#       toLine - fromLine + 1,
#       fromLine
#       ]

def people_profiles2 (csaId, pids):
    pp = ', '.join([ '%s' ] * len(pids))
    return (
            'SELECT ap.from_date, ap.to_date, ap.person_id, a.* FROM account_person ap JOIN account a ON ap.account_id=a.id WHERE ap.person_id in (%s) AND a.csa_id=%%s' % pp,
            'SELECT csa_id, person_id, perm_id FROM permission_grant WHERE person_id IN (%s) AND csa_id=%%s' % pp,
            pids + [ csaId ],
            )

def people_profiles1 (pids):
    pp = ', '.join([ '%s' ] * len(pids))
    return (
            'SELECT * FROM person WHERE id IN (%s)' % pp,
            'SELECT pc.person_id, pc.priority, a.* FROM person_contact pc JOIN contact_address a ON a.id=pc.address_id WHERE pc.person_id IN (%s)' % pp,
            list(pids),
            )

def updateProfile (p):
    return 'UPDATE person SET first_name = %s, middle_name = %s, last_name = %s, account_notifications = %s, cash_treshold = %s WHERE id = %s', [
        p['first_name'],
        p['middle_name'],
        p['last_name'],
        p['account_notifications'],
        p['cash_treshold'],
        p['id'],
        ]

def removeContactAddresses (aids):
    return 'DELETE FROM contact_address WHERE id in (%s)' % ','.join([ '%s' ] * len(aids)), aids

def removePersonContacts (aids):
    return 'DELETE FROM person_contact WHERE address_id in (%s)' % ','.join([ '%s' ] * len(aids)), aids
#    # cfr. http://stackoverflow.com/a/4429409
#    return (
#'''DELETE person_contact p FROM person_contact p,
#          (SELECT pc.id
#           FROM person_contact pc
#           JOIN contact_address a ON pc.address_id = a.id
#           WHERE pc.person_id = %s AND a.kind != %s) t
#    WHERE p.id = t.id''', [ pid, Ck_Id ]
#            )

def saveAddress (addr, kind, ctype):
    return '''INSERT INTO contact_address (address, kind, contact_type) VALUES (%s, %s, %s)''', [ addr, kind, ctype ]

def linkAddress (pid, aid, pri):
    return '''INSERT INTO person_contact (person_id, address_id, priority) VALUES (%s, %s, %s)''', [ pid, aid, pri ]

def fetchContacts (pid):
    return 'SELECT a.id FROM person_contact pc JOIN contact_address a ON pc.address_id=a.id WHERE pc.person_id=%s AND a.kind != %s', [ pid, Ck_Id ]
#    return 'SELECT pc.id, pc.priority, a.id, a.kind, a.address, a.contact_type FROM person_contact pc JOIN contact_address a ON pc.address_id=a.id WHERE pc.person_id=%s ORDER BY pc.priority', [ pid ]

def revokePermissions (pid, csaId, level):
    return (
'''DELETE permission_grant g FROM permission_grant g,
          (SELECT g.id
           FROM permission_grant g
           JOIN permission p ON g.perm_id=p.id
           WHERE g.person_id=%s AND g.csa_id=%s AND p.visibility < %s) t
    WHERE g.id = t.id''', [ pid, csaId, level ])

def grantPermission (pid, perm, csaId):
    return '''INSERT INTO permission_grant (person_id, perm_id, csa_id) VALUES (%s, %s, %s)''', [ pid, perm, csaId ]

def permissionLevel (pid, csaId):
    return '''SELECT MAX(p.visibility) FROM permission p JOIN permission_grant g ON p.id=g.perm_id WHERE g.person_id=%s AND g.csa_id=%s''', [ pid, csaId ]

def isUniqueEmail (pid, email):
    return '''SELECT COUNT(a.id) FROM contact_address a JOIN person_contact pc ON pc.address_id=a.id WHERE pc.person_id != %s AND a.address = %s AND a.kind = %s''', [ pid, email, Ck_Email ]

def checkConn ():
    return 'SELECT 1'

def column_names (cur):
    return [ f[0] for f in cur.description ]

def iter_objects (cur):
    cn = column_names(cur)
    return [ dict(zip(cn, x)) for x in list(cur) ]
