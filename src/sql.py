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
