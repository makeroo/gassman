"""
Created on 03/mar/2014

@author: makeroo
"""


#P_membership = 1
P_canCheckAccounts = 2
P_canAdminPeople = 3 # very low level!
#P_canEnterDeposit = 4 # deprecated
P_canEnterPayments = 5
P_canManageTransactions = 6
P_canEnterCashExchange = 7
#P_canEnterWithdrawal = 8 # deprecated
P_canViewContacts = 9
P_canEditContacts = 10
P_canGrantPermissions = 11
P_canEditMembershipFee = 12
P_csaEditor = 13
P_canCloseAccounts = 14

Tt_Deposit = 'd'         # deprecated,       READ ONLY
Tt_Error = 'e'
Tt_MembershipFee = 'f'   # pagamento quota,  P_canEditMembershipFee
Tt_Generic = 'g'         # deprecated,       READ ONLY
Tt_Payment = 'p'         # pagamento merce,  P_canEnterPayments
Tt_PaymentExpenses = 'q' # deprecated,       READ ONLY (conto EXPENSES invece di KITTY per le spese)
# TODO 'r'
Tt_Trashed = 't'         # cancellata,       P_canManageTransactions or isEditor
Tt_Unfinished = 'u'
Tt_Withdrawal = 'w'      # deprecated,       READ ONLY
Tt_CashExchange = 'x'    # scambio contante, P_canEnterCashExchange
Tt_AccountClosing = 'z'  # chiusura conto,   P_canCloseAccounts

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
Ck_GooglePlusProfile = '+'
Ck_Photo = 'P'

Ckk = set([Ck_Telephone,
           Ck_Mobile,
           Ck_Email,
           Ck_Fax,
           Ck_Id,
           Ck_Nickname,
           Ck_GooglePlusProfile,
           Ck_Photo,
           ])

transactionPermissions = {
#    Tt_Deposit: READ ONLY P_canEnterDeposit,
    Tt_Payment: P_canEnterPayments,
    Tt_CashExchange: P_canEnterCashExchange,
#    Tt_Withdrawal: READ ONLY P_canEnterWithdrawal,
    Tt_MembershipFee: P_canEditMembershipFee,
#    Tt_PaymentExpenses: READ ONLY P_canEnterPayments,
#    Tt_Generic: READ ONLY P_canCheckAccounts,
    }

editableTransactionPermissions = set(transactionPermissions.values())

deletableTransactions = set([
    Tt_Generic,
    Tt_Deposit,
    Tt_Payment,
    Tt_CashExchange,
    Tt_Withdrawal,
    Tt_MembershipFee,
    Tt_PaymentExpenses,
    ])
editableTransactions = set([
#    Tt_Generic,
#    Tt_Deposit,
    Tt_Payment,
    Tt_CashExchange,
#    Tt_Withdrawal,
#    Tt_Trashed,
    Tt_MembershipFee,
#    Tt_PaymentExpenses,
#    Tt_Unfinished,
    ])

Ck_Telephone = 'T'
Ck_Mobile = 'M'
Ck_Email = 'E'
Ck_Fax = 'F'
Ck_Id = 'I'
Ck_Nickname = 'N'
Ck_Picture = 'P'
Ck_GProfile = '+'
Ck_Web = 'W'

As_Open = 'O'
As_Closing = 'C'
As_closeD = 'D'
As_Fusion_pending = 'F'

Tl_Added = 'A'
Tl_Deleted = 'D'
Tl_Modified = 'M'
Tl_Error = 'E'

Tn_kitty_deposit = 'kitty_deposit'
Tn_account_closing = 'account_closing'

At_Asset = 'ASSET' # persone
At_Expense = 'EXPENSE' # spese
At_Income = 'INCOME' # versamenti
At_Kitty = 'KITTY' # kitty

def account_owners (accountId):
    return 'SELECT p.first_name, p.middle_name, p.last_name, p.id, ap.from_date, ap.to_date FROM person p JOIN account_person ap ON ap.person_id=p.id WHERE ap.account_id=%s', [ accountId ]

def account_has_open_owners (accountId):
    return 'SELECT ap.id FROM account_person ap WHERE ap.account_id=%s AND ap.to_date IS NULL', [ accountId ]

def account_description (accountId):
    return 'SELECT a.gc_name, c.name, c.id FROM account a JOIN csa c ON a.csa_id=c.id WHERE a.id=%s', [ accountId ]

def count_account_movements (accountDbId, filterBy):
    q = '''
SELECT count(*)
 FROM transaction t
 JOIN transaction_line l ON l.transaction_id=t.id
 JOIN currency c ON c.id=t.currency_id
 WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND l.account_id=%s
 '''
    a = [ Tt_Unfinished, Tt_Error, accountDbId ]
    if filterBy:
        q += ' AND (l.description LIKE %s OR t.description LIKE %s)'
        a.extend([ filterBy, filterBy ])
    return q, a

def account_movements (accountDbId, filterBy, fromLine, toLine):
    q = '''
SELECT t.description, t.transaction_date, l.description, l.amount, t.id, c.symbol, t.cc_type
 FROM transaction t
 JOIN transaction_line l ON l.transaction_id=t.id
 JOIN currency c ON c.id=t.currency_id
 WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND l.account_id=%s
 '''
    a = [ Tt_Unfinished, Tt_Error, accountDbId ]
    if filterBy:
        q += ' AND (l.description LIKE %s OR t.description LIKE %s)'
        a.extend([ filterBy, filterBy ])
    q += ' ORDER BY t.transaction_date DESC'
    if fromLine is not None:
        q += ' LIMIT %s OFFSET %s'
        a.extend([ toLine - fromLine + 1, fromLine ])
    return q, a

def account_amount (accountDbId, returnCurrencyId=False):
    q = 'SELECT SUM(l.amount), c.symbol'
    if returnCurrencyId:
        q += ', c.id'
    q += """ FROM transaction t
 JOIN transaction_line l ON l.transaction_id=t.id
 JOIN account a on l.account_id=a.id
 JOIN currency c ON c.id=a.currency_id
 WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND l.account_id=%s"""
    return q, [ Tt_Unfinished, Tt_Error, accountDbId ]

accounts_index_order_by = [ 'p.first_name, p.last_name',
                           'ta',
                           'td desc',
                           ]

def accounts_index (csaId, t, dp, o, ex, fromLine, toLine, search_contact_kinds):
    q = '''SELECT p.id, p.first_name, p.middle_name, p.last_name, a.id, sum(l.amount) AS ta, c.symbol, MAX(t.transaction_date) AS td, a.membership_fee
 FROM '''
    a = []

    if t and search_contact_kinds:
        q += '''
  (SELECT p.*, group_concat(ca.address, ', ') AS contacts
   FROM person p
   LEFT JOIN person_contact pc ON pc.person_id=p.id
   LEFT JOIN contact_address ca ON ca.id=pc.address_id
   WHERE ca.kind in %s
   GROUP BY p.id) p'''
        a.append(set(search_contact_kinds))
    else:
        q += 'person p'

    q += '''
 JOIN account_person ap ON ap.person_id=p.id
 JOIN account a on ap.account_id=a.id
 JOIN currency c ON a.currency_id=c.id
 LEFT JOIN transaction_line l ON l.account_id=a.id
 LEFT JOIN transaction t ON t.id=l.transaction_id
 WHERE
 a.csa_id=%s'''
    a.append(csaId)

    if not ex:
        q += ' AND ap.to_date IS NULL'

    q += ''' AND t.modified_by_id IS NULL AND
 (t.cc_type IS NULL OR t.cc_type NOT IN (%s, %s))'''
    a.extend([ Tt_Unfinished, Tt_Error ])

    if t:
        q += ' AND (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s'
        a.extend([ t, t, t ])
        if search_contact_kinds:
            q += ' OR p.contacts LIKE %s)'
            a.append(t)
        else:
            q += ')'

    dp = int(dp)
    if dp == -2:
        q += " AND p.default_delivery_place_id IS NULL"
    elif dp != -1:
        q += " AND p.default_delivery_place_id=%s"
        a.append(dp)

    q += ' GROUP BY p.id, a.id'

    if o:
        q += ' ORDER BY ' + o

    if fromLine != -1:
        q += ''' LIMIT %s OFFSET %s'''
        a.extend([
            toLine - fromLine + 1,
            fromLine
        ])

    return q, a

def check_user (userId, authenticator, kind):
    return 'SELECT p.id, p.first_name, p.middle_name, p.last_name, p.rss_feed_id FROM contact_address c JOIN person_contact pc ON c.id=pc.address_id JOIN person p ON p.id=pc.person_id WHERE c.kind=%s AND c.contact_type=%s AND c.address=%s', [ kind, authenticator, userId ]

def create_contact (addr, kind, contactType):
    return 'INSERT INTO contact_address (address, kind, contact_type) VALUES (%s,%s,%s)', [ addr, kind, contactType ]

def create_person (first, middle, last):
    return 'INSERT INTO person (first_name, middle_name, last_name) VALUES (%s,%s,%s)', [ first, middle, last ]

def assign_rss_feed_id (personId, rss_feed_id):
    return 'UPDATE person SET rss_feed_id=%s WHERE id=%s', [ rss_feed_id, personId ]

def assign_contact (contact, person):
    return 'INSERT INTO person_contact (person_id, address_id) VALUES (%s, %s)', [ person, contact ]

def has_accounts (pid):
    return 'SELECT count(*) FROM account_person WHERE person_id=%s AND to_date IS NULL', [ pid ]

def has_or_had_account (pid, accId):
    return 'SELECT count(*) FROM account_person WHERE person_id=%s AND account_id=%s', [ pid, accId ]

#def find_visible_permissions (personId):
#    return 'SELECT id, name, description FROM permission p WHERE visibility <= (SELECT MAX(p.visibility) FROM permission p JOIN permission_grant g ON p.id=g.perm_id JOIN person u ON g.person_id=u.id WHERE u.id=%s) ORDER BY visibility, ord, name', [ personId ]

def find_user_permissions (personId, csaId):
    return 'SELECT g.perm_id FROM person u JOIN permission_grant g ON g.person_id=u.id WHERE u.id=%s AND g.csa_id=%s', [ personId, csaId ]
    #return 'SELECT p.id FROM person u JOIN permission_grant g ON g.person_id=u.id JOIN permission p ON g.perm_id=p.id WHERE u.id=%s', [ personId ]

def find_user_csa (personId):
    return 'SELECT c.id, c.name, ap.to_date IS NULL AS "active_member" FROM account_person ap JOIN account a ON a.id=ap.account_id JOIN csa c ON c.id=a.csa_id WHERE ap.person_id=%s', [ personId ]

#def find_user_accounts (personId):
#    return 'SELECT a.csa_id, a.id, ap.from_date, ap.to_date FROM account_person ap JOIN account a ON ap.account_id = a.id WHERE ap.person_id = %s ORDER BY a.csa_id, ap.from_date', [ personId ]

# TODO: si ripristina se si fa la pagina di associazione conto...
#def find_users_without_account ():
#    return 'SELECT id, first_name, middle_name, last_name FROM person WHERE current_account_id IS NULL'

def update_last_login (personId, loginTime):
    return 'UPDATE person SET last_login=%s WHERE id=%s', [ loginTime, personId ]

def update_last_visit (personId, visitTime):
    return 'UPDATE person SET last_visit=%s WHERE id=%s', [ visitTime, personId ]

def check_membership_by_kitty (personId, accId):
    return '''
SELECT COUNT(*)
  FROM account kitty
  JOIN account useraccount ON kitty.csa_id=useraccount.csa_id
  JOIN account_person ap   ON ap.account_id=useraccount.id
 WHERE kitty.id=%s AND ap.person_id=%s AND kitty.gc_type=%s and ap.to_date IS NULL
''', [ accId, personId, At_Kitty ]

def is_user_member_of_csa (personId, csaId, stillMember):
    q = 'SELECT COUNT(*) FROM account_person ap JOIN account a ON a.id=ap.account_id WHERE a.csa_id=%s AND ap.person_id=%s'
    a = [ csaId, personId ]
    if stillMember:
        q += ' AND ap.to_date IS NULL'
    return q, a

def has_permission_by_account (perm, personId, accId):
    '''Uso accId solo per determinare la CSA, non verifico che personId abbia intestato accId, anzi in generale non è vero.
    Vedi il caso canCheckAccounts.
    '''
    return 'SELECT count(*) FROM permission_grant g JOIN account a ON a.csa_id=g.csa_id WHERE g.perm_id=%s AND g.person_id=%s AND a.id=%s', [ perm, personId, accId ]
#    return 'SELECT count(*) FROM permission_grant g JOIN account a ON a.csa_id=g.csa_id JOIN account_person ap ON ap.person_id=g.person_id WHERE g.perm_id=%s AND g.person_id=%s AND a.id=%s AND ap.to_date IS NULL', [ perm, personId, accId ]

def has_permission_by_csa (perm, personId, csaId):
    q = 'SELECT count(*) FROM permission_grant WHERE perm_id=%s AND person_id=%s AND csa_id'
    a = [ perm, personId ]
    if csaId is None:
        q += ' IS NULL'
    else:
        q += '=%s'
        a.append(csaId)
    return q, a

def has_permissions (perms, personId, csaId):
    return 'SELECT count(*) FROM permission_grant WHERE perm_id in %s AND person_id=%s AND csa_id=%s', [ set(perms), personId, csaId ]

def transaction_lines (tid):
    return 'SELECT id, account_id, description, amount FROM transaction_line WHERE transaction_id=%s ORDER BY id', [ tid ]

def transaction_people (tid):
    # qui non verifico che acount_person sia del csa giusto perché è implicito nella transazione
    # ma devo verificare che l'inserimento della transazione (quidi transaction_log.log_date e
    # non transaction.transaction_date) ricada nell'intervallo di validità di
    # account_person
    return '''
SELECT DISTINCT l.account_id, ap.person_id
 FROM transaction t
 JOIN transaction_line l ON t.id=l.transaction_id
 JOIN transaction_log log ON log.transaction_id=t.id
 JOIN account_person ap ON ap.account_id=l.account_id
 WHERE t.id=%s AND
       ap.from_date <= log.log_date AND (ap.to_date IS NULL OR ap.to_date >= log.log_date)''', [ tid ]

#SELECT DISTINCT p.id, p.first_name, p.middle_name, p.last_name, l.account_id
# FROM transaction_line l
# JOIN account_person ap ON ap.account_id=l.account_id
# JOIN person p ON ap.person_id=p.id
# WHERE transaction_id=%s AND ap.to_date IS NULL''', [ tid ]

#def transaction_account_gc_names (tid):
#    return 'SELECT DISTINCT a.id, a.gc_name, c.symbol FROM transaction_line l JOIN account a ON a.id=l.account_id JOIN currency c ON c.id=a.currency_id WHERE transaction_id=%s', [ tid ]

def rss_feed (rssId):
    return 'SELECT t.description, t.transaction_date, l.amount, l.id, c.symbol FROM transaction_line l JOIN transaction t ON t.id=l.transaction_id JOIN account_person ap ON ap.account_id=l.account_id JOIN account a ON l.account_id=a.id JOIN person p ON p.id=ap.person_id JOIN currency c ON c.id=a.currency_id WHERE p.rss_feed_id=%s AND ap.to_date IS NULL AND t.cc_type NOT IN (%s, %s) ORDER BY t.transaction_date DESC LIMIT 8', [ rssId, Tt_Unfinished, Tt_Error ]

def rss_user (rssId):
    return 'SELECT first_name, middle_name, last_name FROM person WHERE rss_feed_id=%s', [ rssId ]

#def rss_id (personId):
#    return 'SELECT rss_feed_id FROM person WHERE id=%s', [ personId ]

def csa_info (csaId):
    return 'SELECT * FROM csa WHERE id=%s', [ csaId ]

def csa_by_account (accId):
    return 'SELECT csa_id FROM account WHERE id=%s', [ accId ]

def csa_update (csa):
    return '''UPDATE csa SET name=%s, description=%s, default_account_threshold=%s WHERE id=%s''', [
        csa['name'],
        csa['description'],
        csa['default_account_threshold'],
        csa['id'],
    ]

def csa_amount (csaId):
    return 'SELECT SUM(l.amount), c.symbol FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id JOIN account a ON l.account_id=a.id JOIN currency c ON c.id=a.currency_id WHERE t.modified_by_id IS NULL AND t.cc_type NOT IN (%s, %s) AND a.gc_type in (%s, %s) AND a.csa_id=%s GROUP BY c.symbol', [ Tt_Unfinished, Tt_Error, At_Asset, At_Kitty, csaId ]

#def csa_account_by_account (referenceAccId, accountType):
#    return 'SELECT b.id FROM account a JOIN account b ON a.csa_id=b.csa_id WHERE a.id=%s AND b.gc_type=%s', [ referenceAccId, accountType ]

def csa_account (csaId, accountType, currencyId=None, accId=None, full=False):
    q = 'SELECT '
    q += 'a.*' if full else 'a.id'
    q += ' FROM account a WHERE a.csa_id=%s AND a.gc_type=%s'
    a = [ csaId, accountType ]
    if currencyId is not None:
        q += ' AND a.currency_id=%s'
        a.append(currencyId)
    if accId is not None:
        q += ' AND id=%s'
        a.append(accId)
    return q, a

def csa_last_kitty_deposit (kittyId):
    return '''
SELECT l.log_date, t.id as tid, p.id, p.first_name, p.middle_name, p.last_name
 FROM transaction_log l
 JOIN transaction t ON t.id = l.transaction_id
 JOIN transaction_line tl ON tl.transaction_id = t.id
 JOIN person p ON p.id = l.operator_id
 WHERE l.op_type = %s AND l.notes = %s AND tl.account_id = %s
       AND t.modified_by_id IS NULL
 ORDER BY l.log_date
 LIMIT %s''', [
  Tl_Added,
  Tn_kitty_deposit,
  kittyId,
  1,
  ]

def csa_list (pid):
    return 'SELECT c.id, c.name, c.description, g.id AS "belong" FROM csa c LEFT JOIN permission_grant g ON g.person_id=%s WHERE g.csa_id IS NULL OR g.csa_id=c.id', [ pid ]

def csa_delivery_places (csaId):
    return '''
SELECT p.id, p.description, a.first_line, a.second_line, a.description as addr_description,
       IF(a.zip_code IS NULL, c.zip_code, a.zip_code) as zip_code, c.name as city, s.name as state
 FROM delivery_place p
 JOIN street_address a ON p.address_id=a.id
 JOIN city c ON a.city_id=c.id
 JOIN state s ON c.state_id=s.id
 WHERE p.csa_id = %s''', [ csaId ]

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

def account_owners_with_optional_email_for_notifications (accountIds):
    return '''
SELECT ap.account_id, p.id, p.first_name, p.middle_name, p.last_name, c.address
 FROM account_person ap
 JOIN person p ON ap.person_id=p.id
 LEFT JOIN person_contact pc ON p.id=pc.person_id
 LEFT JOIN contact_address c ON pc.address_id=c.id
 WHERE ap.to_date IS NULL AND
       ap.account_id IN %s AND
       (c.kind=%s OR c.kind IS NULL) AND
       p.account_notifications=%s
 ORDER BY ap.account_id, pc.priority''', [ set(accountIds), Ck_Email, An_EveryMovement ]

def account_total_for_notifications (accountIds):
    return '''
SELECT a.id, sum(l.amount), c.symbol
 FROM account a
 JOIN currency c ON a.currency_id=c.id
 JOIN transaction_line l ON l.account_id=a.id
 JOIN transaction t ON t.id=l.transaction_id

 WHERE
 t.modified_by_id IS NULL AND
 t.cc_type NOT IN (%s, %s) AND
 a.id IN %s

 GROUP BY a.id
''', [ Tt_Unfinished, Tt_Error, set(accountIds) ]

def account_updateMembershipFee (csaId, personId, amount):
    return '''
UPDATE account a
 INNER JOIN account_person ap ON a.id=ap.account_id
 SET a.membership_fee = %s
 WHERE ap.person_id = %s AND ap.to_date IS NULL AND a.csa_id = %s''', [ amount, personId, csaId ]

def account_close (closeDatetime, accountId, ownerId):
    return 'UPDATE account_person SET to_date=%s WHERE person_id=%s AND account_id = %s AND to_date IS NULL', [ closeDatetime, ownerId, accountId ]

#def expenses_accounts (csaId):
#    return 'SELECT id, gc_name, currency_id FROM account where gc_type =%s AND csa_id=%s AND state=%s', [ At_Expense, csaId, As_Open]

#def expenses_line_descriptions (csaId):
#    return 'SELECT DISTINCT l.description FROM transaction_line l JOIN account a ON l.account_id=a.id WHERE a.gc_type=%s AND a.csa_id=%s AND l.description IS NOT NULL', [ At_Expense, csaId ]

#def expenses_transaction_descriptions (csaId):
#    return 'SELECT DISTINCT t.description FROM transaction_line l JOIN account a ON l.account_id=a.id JOIN transaction t ON l.transaction_id=t.id WHERE a.gc_type=%s AND a.csa_id=%s AND t.description IS NOT NULL', [ At_Expense, csaId ]

def insert_transaction (desc, tDate, ccType, currencyId, csaId):
    return 'INSERT INTO transaction (description, transaction_date, cc_type, currency_id, csa_id) SELECT %s, %s, %s, id, %s FROM currency WHERE id=%s', [ desc, tDate, ccType, csaId, currencyId ]

def insert_transaction_line (tid, desc, amount, accId):
    return 'INSERT INTO transaction_line (transaction_id, account_id, description, amount) SELECT %s, a.id, %s, %s FROM account a WHERE a.id = %s', [ tid, desc, amount, accId ]

def insert_transaction_line_membership_fee (tid, amount, csaId, currencyId):
    return '''
INSERT INTO transaction_line (transaction_id, account_id, description, amount)
 SELECT %s, a.id, %s, - a.membership_fee * %s
  FROM account a
  JOIN account_person ap on ap.account_id=a.id
  WHERE a.csa_id = %s AND a.currency_id = %s AND a.gc_type = %s AND a.membership_fee > 0
    AND ap.to_date IS NULL
  GROUP BY a.id
  ''', [ tid, '', amount, csaId, currencyId, At_Asset ]

def check_transaction_coherency (tid):
    return 'SELECT DISTINCT a.currency_id, a.csa_id FROM transaction_line l JOIN account a ON a.id=l.account_id WHERE l.transaction_id = %s', [ tid ]

def transaction_calc_last_line_amount (tid, tlineId):
    return 'SELECT - SUM(amount) FROM transaction_line WHERE transaction_id = %s AND id != %s', [ tid, tlineId ]

def transaction_fix_amount (tlineId, amount):
    return 'UPDATE transaction_line SET amount = %s WHERE id = %s', [ amount, tlineId ]

def finalize_transaction (tid, ttype):
    return 'UPDATE transaction SET cc_type=%s WHERE id=%s', [ ttype, tid ]

def transaction_fetch_lines_to_compare (oldTrans, newTrans):
    '''Metodo usato per calcolare le differenze introdotte dalla modifica di una transazione.
    '''
    return 'SELECT transaction_id, account_id, amount, description FROM transaction_line WHERE transaction_id in (%s, %s)', [ oldTrans, newTrans ]

def transaction_edit (tid):
    return '''
SELECT t.description, t.transaction_date as date, t.cc_type, c.id as "currency[__cid", c.symbol as "currency[__csym", t.modified_by_id as modified_by, t2.id as "modifies", l.log_date, l.op_type, p.id as operator__pid, p.first_name as operator__first_name, p.middle_name as operator__middle_name, p.last_name as operator__last_name
 FROM transaction t
 JOIN transaction_log l ON l.transaction_id=t.id
 JOIN person p ON l.operator_id = p.id
 LEFT JOIN transaction t2 ON t.id=t2.modified_by_id
 JOIN currency c ON c.id=t.currency_id
 WHERE t.id=%s''', [ tid ]

def log_transaction (tid, opId, logType, logDesc, tDate):
    return 'INSERT INTO transaction_log (log_date, operator_id, op_type, transaction_id, notes) VALUES (%s, %s, %s, %s, %s)', [ tDate, opId, logType, tid, logDesc ] 

def log_transaction_check_operator (personId, transId):
    return 'SELECT COUNT(*) FROM transaction_log WHERE transaction_id=%s AND operator_id=%s', [ transId, personId ]

def transaction_on_kitty_and_user_is_member (transId, personId):
    return '''
SELECT count(*)
  FROM transaction_line l
  JOIN account a ON l.account_id=a.id
  JOIN account a2 ON a.csa_id=a2.csa_id
  JOIN account_person ap ON a2.id=ap.account_id
 WHERE transaction_id=%s AND a.gc_type=%s AND ap.person_id=%s AND ap.to_date IS NULL;
    ''', [ transId, At_Kitty, personId]

def transaction_is_involved (transId, personId):
    return '''
SELECT COUNT(*)
  FROM transaction_line l
  JOIN account a ON l.account_id=a.id
  JOIN account_person ap ON a.id=ap.account_id
 WHERE l.transaction_id=%s AND ap.person_id=%s
''', [ transId, personId ]

def transaction_previuos (transId):
    return 'SELECT id FROM transaction WHERE modified_by_id = %s', [ transId ]

def transaction_type (transId):
    return 'SELECT cc_type, description, modified_by_id FROM transaction WHERE id = %s', [ transId ]

def update_transaction (oldTid, newTid):
    return 'UPDATE transaction SET modified_by_id = %s WHERE id = %s', [ newTid, oldTid ]

transactions_editable_order_by = [ 'l.log_date DESC',
                           't.transaction_date DESC',
                           'p.first_name,p.last_name',
                           't.description'
                           ]

def transactions_count_all (csaId, q):
    return '''SELECT count(l.id)
     FROM transaction_log l
     JOIN transaction t ON t.id=l.transaction_id
     JOIN person p ON l.operator_id= p.id

     WHERE t.csa_id=%s AND l.op_type IN (%s, %s, %s) AND
      (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s OR t.description LIKE %s)
      ''', [
            csaId,
            'A', 'M', 'D',
            q, q, q, q,
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

def transactions_count_by_editor (csaId, operator, q):
    return '''SELECT count(l.id)
     FROM transaction_log l
     JOIN transaction t ON t.id=l.transaction_id
     JOIN person p ON l.operator_id= p.id

     WHERE t.csa_id=%s AND l.operator_id=%s AND l.op_type IN (%s, %s, %s) AND
      (t.description LIKE %s)''', [
            csaId,
            operator,
            'A', 'M', 'D',
            q,
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
            operator,
            'A', 'M', 'D',
            q,
            toLine - fromLine + 1,
            fromLine
            ]

def count_people (csaId, t, dp, ex, search_contact_kinds):
    q = 'SELECT count(p.id) FROM '
    a = []

    if t and search_contact_kinds:
        q += '''
  (SELECT p.*, group_concat(ca.address, ', ') AS contacts
   FROM person p
   LEFT JOIN person_contact pc ON pc.person_id=p.id
   LEFT JOIN contact_address ca ON ca.id=pc.address_id
   WHERE ca.kind in %s
   GROUP BY p.id) p'''
        a.append(set(search_contact_kinds))
    else:
        q += 'person p'

    q += '''
 JOIN account_person ap ON ap.person_id=p.id
 JOIN account a ON a.id=ap.account_id
 WHERE a.csa_id=%s'''
    a.append(csaId)

    if not ex:
       q += ' AND ap.to_date IS NULL'

    if t:
        q += ' AND (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s'
        a.extend([ t, t, t ])
        if search_contact_kinds:
            q += ' OR p.contacts LIKE %s)'
            a.append(t)
        else:
            q += ')'

    dp = int(dp)
    if dp == -2:
        q += " AND p.default_delivery_place_id IS NULL"
    elif dp != -1:
        q += " AND p.default_delivery_place_id=%s"
        a.append(dp)

    return q, a


def people_index (csaId, t, dp, o, ex, fromLine, toLine, search_contact_kinds):
    q = 'SELECT p.id, p.first_name, p.middle_name, p.last_name FROM '
    a = []

    if t and search_contact_kinds:
        q += '''
  (SELECT p.*, group_concat(ca.address, ', ') AS contacts
     FROM person p
LEFT JOIN person_contact pc ON pc.person_id=p.id
LEFT JOIN contact_address ca ON ca.id=pc.address_id
    WHERE ca.kind IN %s
 GROUP BY p.id) p'''
        a.append(set(search_contact_kinds))
    else:
        q += 'person p'

    q += '''
 JOIN account_person ap ON ap.person_id=p.id
 JOIN account a ON a.id=ap.account_id
 WHERE a.csa_id=%s'''
    a.append(csaId)

    if not ex:
       q += ' AND ap.to_date IS NULL'

    if t:
        q += ' AND (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s'
        a.extend([ t, t, t ])
        if search_contact_kinds:
            q += ' OR p.contacts LIKE %s)'
            a.append(t)
        else:
            q += ')'

    dp = int(dp)
    if dp == -2:
        q += " AND p.default_delivery_place_id IS NULL"
    elif dp != -1:
        q += " AND p.default_delivery_place_id=%s"
        a.append(dp)

    if o:
        q += ''' ORDER BY ''' + o

    if fromLine != -1:
        q += ''' LIMIT %s OFFSET %s'''
        a.extend([
           toLine - fromLine + 1,
           fromLine
        ])

    return q, a

def people_profiles2 (csaId, pids):
    return (
            'SELECT ap.from_date, ap.to_date, ap.person_id, a.* FROM account_person ap JOIN account a ON ap.account_id=a.id WHERE ap.person_id in %s AND a.csa_id=%s',
            'SELECT csa_id, person_id, perm_id FROM permission_grant WHERE person_id IN %s AND csa_id=%s',
            [ set(pids), csaId ],
            )

def people_profiles1 (pids):
    return (
            'SELECT * FROM person WHERE id IN %s',
            'SELECT pc.person_id, pc.priority, a.* FROM person_contact pc JOIN contact_address a ON a.id=pc.address_id WHERE pc.person_id IN %s ORDER BY pc.priority',
            [ set(pids) ],
            )

def person_notification_email (pid):
    return '''
SELECT c.address
 FROM person p
 JOIN person_contact pc ON p.id=pc.person_id
 JOIN contact_address c ON pc.address_id=c.id
 WHERE c.kind=%s AND p.id=%s ORDER BY pc.priority LIMIT 1''', [
        Ck_Email, pid
    ]

def updateProfile (p):
    return 'UPDATE person SET first_name = %s, middle_name = %s, last_name = %s, account_notifications = %s, cash_treshold = %s, default_delivery_place_id = %s WHERE id = %s', [
        p['first_name'],
        p['middle_name'],
        p['last_name'],
        p['account_notifications'],
        p['cash_treshold'],
        p['default_delivery_place_id'],
        p['id'],
        ]

def removeContactAddress (aId):
    return 'DELETE FROM contact_address WHERE id=%s', [ aId ]

def removePersonContact (pcId):
    return 'DELETE FROM person_contact WHERE id=%s', [ pcId ]

def removeContactAddresses (aids):
    return 'DELETE FROM contact_address WHERE id in %s', [ set(aids) ]

def removePersonContacts (aids):
    return 'DELETE FROM person_contact WHERE address_id in %s', [ set(aids) ]
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

def updateAddress (pk, addr, ctype):
    return '''UPDATE contact_address SET address=%s, contact_type=%s WHERE id=%s''', [ addr, ctype, pk ]

def linkAddress (pid, aid, pri):
    return '''INSERT INTO person_contact (person_id, address_id, priority) VALUES (%s, %s, %s)''', [ pid, aid, pri ]

def fetchContacts (pid):
    return 'SELECT a.id FROM person_contact pc JOIN contact_address a ON pc.address_id=a.id WHERE pc.person_id=%s AND a.kind != %s', [ pid, Ck_Id ]
#    return 'SELECT pc.id, pc.priority, a.id, a.kind, a.address, a.contact_type FROM person_contact pc JOIN contact_address a ON pc.address_id=a.id WHERE pc.person_id=%s ORDER BY pc.priority', [ pid ]

def fetchAllContacts (pid):
    return 'SELECT pc.id, a.id, a.kind, a.contact_type, a.address FROM person_contact pc JOIN contact_address a ON pc.address_id=a.id WHERE pc.person_id=%s', [ pid ]

def revokePermissions (pid, csaId, pp):
    return (
'''DELETE permission_grant g FROM permission_grant g,
          (SELECT g.id
           FROM permission_grant g
           JOIN permission p ON g.perm_id=p.id
           WHERE g.person_id=%s AND g.csa_id=%s AND p.id in %s) t
    WHERE g.id = t.id''', [ pid, csaId, pp ])

def grantPermission (pid, perm, csaId):
    return '''INSERT INTO permission_grant (person_id, perm_id, csa_id) VALUES (%s, %s, %s)''', [ pid, perm, csaId ]

#def permissionLevel (pid, csaId):
#    return '''SELECT MAX(p.visibility) FROM permission p JOIN permission_grant g ON p.id=g.perm_id WHERE g.person_id=%s AND g.csa_id=%s''', [ pid, csaId ]

def isUniqueEmail (pid, email):
    return '''SELECT COUNT(a.id) FROM contact_address a JOIN person_contact pc ON pc.address_id=a.id WHERE pc.person_id != %s AND a.address = %s AND a.kind = %s''', [ pid, email, Ck_Email ]

admin_people_index_order_by = [
    None, # nessun ordinamento
    'p.last_visit desc',
    'p.first_name, p.last_name',
    'p.last_login',
]

def admin_people_index (t, csaId, order, fromLine, toLine, search_contact_kinds):
    q = 'SELECT p.id, p.first_name, p.middle_name, p.last_name FROM '
    a = []

    if t and search_contact_kinds:
        q += '''
  (SELECT p.*, group_concat(ca.address, ', ') AS contacts
     FROM person p
LEFT JOIN person_contact pc ON pc.person_id=p.id
LEFT JOIN contact_address ca ON ca.id=pc.address_id
    WHERE ca.kind IN %s
 GROUP BY p.id) p'''
        a.append(set(search_contact_kinds))
    else:
        q += 'person p'

    q += '''
 WHERE p.id NOT IN
  (SELECT person_id
     FROM account_person'''
    if csaId:
        q += ' JOIN accont a WHERE a.csa_id=%s'
        a.append(csaId)
    q += ')'

    if t:
        q += ' AND (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s'
        a.extend([t, t, t])
        if search_contact_kinds:
            q += ' OR p.contacts LIKE %s)'
            a.append(t)
        else:
            q += ')'

    if order:
        q += ' ORDER BY ' + order

    if fromLine is not None:
        q += ' LIMIT %s OFFSET %s'
        a.extend([ toLine - fromLine + 1, fromLine ])

    return q, a

def admin_count_people (t, csaId, search_contact_kinds):
    q = 'SELECT count(*) FROM '
    a = []

    if t and search_contact_kinds:
        q += '''
  (SELECT p.*, group_concat(ca.address, ', ') AS contacts
     FROM person p
LEFT JOIN person_contact pc ON pc.person_id=p.id
LEFT JOIN contact_address ca ON ca.id=pc.address_id
    WHERE ca.kind IN %s
 GROUP BY p.id) p'''
        a.append(set(search_contact_kinds))
    else:
        q += 'person p'

    q += '''
 WHERE p.id NOT IN
  (SELECT person_id
     FROM account_person'''
    if csaId:
        q += ' JOIN accont a WHERE a.csa_id=%s'
        a.append(csaId)
    q += ')'

    if t:
        q += ' AND (p.first_name LIKE %s OR p.middle_name LIKE %s OR p.last_name LIKE %s'
        a.extend([t, t, t])
        if search_contact_kinds:
            q += ' OR p.contacts LIKE %s)'
            a.append(t)
        else:
            q += ')'

    return q, a

def reassignContacts (newpid, oldpid):
    return 'UPDATE person_contact SET person_id=%s WHERE person_id=%s', [ newpid, oldpid ]

def reassignPermissions (newpid, oldpid):
    return 'UPDATE permission_grant SET person_id=%s WHERE person_id=%s', [ newpid, oldpid ]

def reassignAccounts (newpid, oldpid):
    return 'UPDATE account_person SET person_id=%s WHERE person_id=%s', [ newpid, oldpid ]

def deletePerson (pid):
    return 'DELETE FROM person WHERE id=%s', [ pid ]

def deleteContactsOfPerson (pid):
    return 'DELETE FROM contact_address WHERE id IN (SELECT address_id FROM person_contact WHERE person_id=%s)', [ pid ]

def deleteContactsPerson (pid):
    return 'DELETE FROM person_contact WHERE person_id=%s', [ pid ]

def deletePermissions (pid):
    return 'DELETE FROM permission_grant WHERE person_id=%s', [ pid ]

def grantAccount (pid, acc, fromDate):
    return 'INSERT INTO account_person (person_id, account_id, from_date) VALUES (%s, %s, %s)', [ pid, acc, fromDate ]

def checkConn ():
    return 'SELECT 1'

def column_names (cur):
    return [ f[0] for f in cur.description ]

def iter_objects (cur):
    cn = column_names(cur)
    return [ dict(zip(cn, x)) for x in list(cur) ]

def fetch_object (cur, returnIfNone=None):
    v = cur.fetchone()
    return dict(zip(column_names(cur), v)) if v else returnIfNone

def fetch_struct (cur):
    def seqmode (c, k, v):
        c.append(v)
        return v
    def mapmode (c, k, v):
        return c.setdefault(k, v)
    seqmode.value = lambda: []
    mapmode.value = lambda: {}
    r = {}
    row = cur.fetchone()
    if row is None:
        raise Exception('no rows feched')
    for k, v in zip(column_names(cur), row):
        pp = k.split('__')
        if len(pp) > 1:
            t = r
            mode = mapmode
            nextmode = None
            for p in pp[:-1]:
                if p.endswith('['):
                    p = p[:-1]
                    nextmode = seqmode
                else:
                    nextmode = mapmode
                t = mode(t, p, nextmode.value())
                mode = nextmode
            mode(t, pp[-1], v)
        else:
            r[k] = v
    return r
