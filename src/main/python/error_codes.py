'''
Created on 14/mag/2014

@author: makeroo
'''

E_ok=''

E_not_authenticated = 'not authenticated'
E_illegal_payload = 'illegal payload'
E_permission_denied = 'permission denied'
E_already_modified = 'already modified' # transaction.id
E_type_mismatch = 'type mismatch'
E_no_lines = 'no lines'
E_illegal_currency = 'illegal currency'
E_illegal_update = 'illegal update'
E_trashed_transactions_can_not_have_lines = 'trashed transactions can not have lines'
E_missing_trashId_of_transaction_to_be_deleted = 'missing trashId of transaction to be deleted'
E_illegal_transaction_type = 'illegal transaction type'
E_illegal_receiver = 'illegal receiver'
#            raise Exception(tlogDesc)
E_accounts_do_not_belong_to_csa = 'accounts do not belong to csa'
E_accounts_not_omogeneous_for_currency_and_or_csa = 'accounts not omogeneous for currency and/or csa'
E_negative_amount = 'negative amount'