import logging
import datetime

import jsonlib

from . import JsonBaseHandler, GDataException
from ..templateutils import shortDate

import error_codes

import gassman_settings as settings


log_gassman = logging.getLogger('gassman.backend')


def insert_close_account_transaction(cur, sql_factory, from_acc_id, now, tdesc, operator_id, dest_acc_id=None):
    cur.execute(*sql_factory.account_amount(from_acc_id, return_currency_id=True))
    v = cur.fetchone()
    amount = v[0] or 0.0
    currency_id = v[2]

    if amount == 0.0:
        return None

    cur.execute(*sql_factory.csa_by_account(from_acc_id))
    csa_id = cur.fetchone()[0]

    if dest_acc_id is None:
        cur.execute(*sql_factory.csa_account(
            csa_id, sql_factory.At_Kitty, currency_id
        ))
        dest_acc_id = cur.fetchone()[0]
    else:
        cur.execute(*sql_factory.csa_by_account(dest_acc_id))
        dest_csa_id = cur.fetchone()[0]
        if csa_id != dest_csa_id:
            raise Exception('From and dest accounts does belong to different CSA')

    cur.execute(*sql_factory.insert_transaction(
        tdesc,
        now,
        sql_factory.Tt_AccountClosing,
        currency_id,
        csa_id
    ))
    tid = cur.lastrowid
    cur.execute(*sql_factory.insert_transaction_line(tid, '', amount, dest_acc_id))
    cur.execute(*sql_factory.insert_transaction_line(tid, '', -amount, from_acc_id))
    last_line_id = cur.lastrowid
    cur.execute(*sql_factory.transaction_calc_last_line_amount(tid, last_line_id))
    a = cur.fetchone()[0]
    # involvedAccounts[lastacc_id] = str(a)
    cur.execute(*sql_factory.transaction_fix_amount(last_line_id, a))

    cur.execute(*sql_factory.log_transaction(
        tid,
        operator_id,
        sql_factory.Tl_Added,
        sql_factory.Tn_account_closing,
        now
    ))

    return tid


class TransactionEditHandler (JsonBaseHandler):
    def do(self, cur, csa_id, trans_id):
        uid = self.current_user
        cur.execute(*self.application.conn.sql_factory.transaction_edit(trans_id))

        r = self.application.conn.sql_factory.fetch_struct(cur)
        r['transId'] = trans_id

        cc_type = r['cc_type']
        # regole per editare:
        # è D, ho P_canEnterDeposit e l'ho creata io
        # è P, ho P_canEnterPayments e l'ho creata io
        # oppure P_canManageTransactions
        if (not self.application.has_permissions(
                cur,
                [self.application.conn.sql_factory.P_canManageTransactions,
                 self.application.conn.sql_factory.P_canCheckAccounts
                 ],
                uid, csa_id) and
            not self.application.is_kitty_transition_and_is_member(cur, trans_id, uid) and
            not (cc_type in self.application.conn.sql_factory.editableTransactions and
                 self.application.has_permission_by_csa(
                     cur,
                     self.application.conn.sql_factory.transactionPermissions.get(cc_type),
                     uid, csa_id) and
                 self.application.is_transaction_editor(cur, trans_id, uid)
                 ) and
            not self.application.isInvolvedInTransaction(cur, trans_id, uid)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)

        p = self.payload
        cur.execute(*self.application.conn.sql_factory.transaction_lines(trans_id))
        r['lines'] = [dict(account=l[1], notes=l[2], amount=l[3]) for l in cur]

        account_people_index = {}
        r['people'] = account_people_index
        cur.execute(*self.application.conn.sql_factory.transaction_people(trans_id))
        for acc_id, person_id, from_date, to_date in cur.fetchall():
            pp = account_people_index.setdefault(acc_id, [])
            pp.append([person_id, from_date, to_date])
        if p.get('fetchKitty'):
            cur.execute(*self.application.conn.sql_factory.csa_account(
                csa_id, self.application.conn.sql_factory.At_Kitty, full=True
            ))
            r['kitty'] = {
                x['id']: x for x in self.application.conn.sql_factory.iter_objects(cur)
                }

        return r


class TransactionSaveHandler (JsonBaseHandler):
    notifyExceptions = True

    def do(self, cur, csa_id):
        # involvedAccounts = dict()

        csa_id = int(csa_id)
        uid = self.current_user
        tdef = self.payload
        trans_id = tdef.get('transId', None)
        ttype = tdef['cc_type']
        tcurr = tdef['currency']
        tlines = tdef['lines']
        tdate = jsonlib.decode_date(tdef['date'])
        tdesc = tdef['description']
        # tlogtype = None  # la metto qua per prospetto completo ma è ridefinita dopo
        tlogdesc = error_codes.E_ok
        if tdate is None:
            tdate = datetime.datetime.utcnow()
        if trans_id is None:
            old_cc = None
            old_desc = None
        else:
            trans_id = int(trans_id)
            cur.execute(*self.application.conn.sql_factory.transaction_type(trans_id))
            old_cc, old_desc, modifiedBy = cur.fetchone()
            if modifiedBy is not None:
                raise GDataException(error_codes.E_already_modified)

        if ttype in (
                self.application.conn.sql_factory.Tt_Deposit,
                self.application.conn.sql_factory.Tt_CashExchange,
                self.application.conn.sql_factory.Tt_Withdrawal,
                self.application.conn.sql_factory.Tt_MembershipFee,
                self.application.conn.sql_factory.Tt_Payment
        ):
            if old_cc is not None and old_cc != ttype:
                raise GDataException(error_codes.E_type_mismatch)
            if len(tlines) == 0:
                raise GDataException(error_codes.E_no_lines)
            if ((not self.application.has_permission_by_csa(
                    cur, self.application.conn.sql_factory.transactionPermissions[ttype], uid, csa_id
                 ) or
                (trans_id is not None and not self.application.is_transaction_editor(cur, trans_id, uid))) and
                not self.application.has_permission_by_csa(
                    cur, self.application.conn.sql_factory.P_canManageTransactions, uid, csa_id
                )):
                raise GDataException(error_codes.E_permission_denied)

            # verifico che tdate sia all'interno di tutti gli intervalli di intestazione o meglio:
            # per ogni conto, raccatto le sue intestazioni e verifico che almeno una comprenda la data
            cur.execute(
                *self.application.conn.sql_factory.check_date_against_account_ownerships(
                    [l['account'] for l in tlines],  # involved accounts
                    tdate
                )
            )
            if len(cur.fetchall()) > 0:
                raise GDataException(error_codes.E_transaction_date_outside_ownership_range)

            cur.execute(*self.application.conn.sql_factory.insert_transaction(
                tdesc, tdate, self.application.conn.sql_factory.Tt_Unfinished, tcurr, csa_id
            ))
            tid = cur.lastrowid
            if tid == 0:
                raise GDataException(error_codes.E_illegal_currency)

            custom_csa_accounts = dict(
                EXPENSE=None,
                INCOME=None,
                KITTY=None
            )
            for l in tlines:
                desc = l['notes']
                amount = l['amount']
                req_acc_id = l['account']
                if req_acc_id in custom_csa_accounts:
                    acc_id = custom_csa_accounts[req_acc_id]
                    if acc_id is None:
                        cur.execute(*self.application.conn.sql_factory.csa_account(csa_id, req_acc_id, tcurr))
                        acc_id = cur.fetchone()[0]
                        custom_csa_accounts[req_acc_id] = acc_id
                else:
                    acc_id = req_acc_id
                cur.execute(*self.application.conn.sql_factory.insert_transaction_line(tid, desc, amount, acc_id))
                last_line_id = cur.lastrowid

            cur.execute(*self.application.conn.sql_factory.check_transaction_coherency(tid))
            v = list(cur)
            if len(v) != 1:
                ttype = self.application.conn.sql_factory.Tt_Error
                tlogtype = self.application.conn.sql_factory.Tl_Error
                tlogdesc = error_codes.E_accounts_not_omogeneous_for_currency_and_or_csa
            elif v[0][1] != csa_id:
                ttype = self.application.conn.sql_factory.Tt_Error
                tlogtype = self.application.conn.sql_factory.Tl_Error
                tlogdesc = error_codes.E_accounts_do_not_belong_to_csa
            else:
                cur.execute(*self.application.conn.sql_factory.transaction_calc_last_line_amount(tid, last_line_id))
                a = cur.fetchone()[0]
                # involvedAccounts[lastAccId] = str(a)
                cur.execute(*self.application.conn.sql_factory.transaction_fix_amount(last_line_id, a))
                tlogtype = self.application.conn.sql_factory.Tl_Added if trans_id is None \
                    else self.application.conn.sql_factory.Tl_Modified

        elif ttype == self.application.conn.sql_factory.Tt_Trashed:
            if old_cc not in self.application.conn.sql_factory.deletableTransactions:
                raise GDataException(error_codes.E_illegal_delete)
            if len(tlines) > 0:
                raise GDataException(error_codes.E_trashed_transactions_can_not_have_lines)
            if trans_id is None:
                raise GDataException(error_codes.E_missing_trashId_of_transaction_to_be_deleted)
            if ((not self.application.has_permissions(
                    cur, self.application.conn.sql_factory.editableTransactionPermissions, uid, csa_id
                 ) or
                not self.application.is_transaction_editor(cur, trans_id, uid)) and
                not self.application.has_permission_by_csa(
                    cur, self.application.conn.sql_factory.P_canManageTransactions, uid, csa_id
                )):
                raise GDataException(error_codes.E_permission_denied)

            # verifico che tdate sia all'interno di tutti gli intervalli di intestazione o meglio:
            # per ogni conto, raccatto le sue intestazioni e verifico che almeno una comprenda la data
            cur.execute(
                *self.application.conn.sql_factory.check_date_against_account_ownerships_by_trans(trans_id, tdate)
            )
            if len(cur.fetchall()) > 0:
                raise GDataException(error_codes.E_transaction_date_outside_ownership_range)

            cur.execute(*self.application.conn.sql_factory.insert_transaction(
                tdesc, tdate, self.application.conn.sql_factory.Tt_Unfinished, tcurr, csa_id
            ))
            tid = cur.lastrowid
            if tid == 0:
                raise GDataException(error_codes.E_illegal_currency)
            tlogtype = self.application.conn.sql_factory.Tl_Deleted
            # tlogdesc = ''
        else:
            log_gassman.error('illegal transaction type: %s', tdef)
            raise GDataException(error_codes.E_illegal_transaction_type)

        cur.execute(*self.application.conn.sql_factory.finalize_transaction(tid, ttype))
        cur.execute(*self.application.conn.sql_factory.log_transaction(
            tid, uid, tlogtype, tlogdesc, datetime.datetime.utcnow()
        ))
        if trans_id is not None and ttype != self.application.conn.sql_factory.Tt_Error:
            cur.execute(*self.application.conn.sql_factory.update_transaction(trans_id, tid))
        if ttype == self.application.conn.sql_factory.Tt_Error:
            raise GDataException(tlogdesc)
        else:
            self.notify_account_change(cur, tid, tdesc, tdate, trans_id, old_desc)
        return tid

    # Transaction notification types
    Tnt_new_transaction = 'n'
    Tnt_amount_changed = 'a'
    Tnt_notes_changed = 'd'
    Tnt_transaction_removed = 'r'
    Tnt_description_changed = 'm'

    def notify_account_change(self, cur, trans_id, tdesc, tdate, modified_trans_id, old_desc):
        cur.execute(*self.application.conn.sql_factory.transaction_fetch_lines_to_compare(modified_trans_id, trans_id))
        oldLines = dict()
        newLines = dict()
        diffs = dict()
        lines = {
            trans_id: newLines,
            modified_trans_id: oldLines,
        }
        for trans, acc_id, amount, lineDesc in cur.fetchall():
            lines[trans][acc_id] = (amount, lineDesc)
        for acc_id, newp in newLines.items():
            oldp = oldLines.get(acc_id)
            if oldp is None:
                diffs[acc_id] = [self.Tnt_new_transaction, newp[0], newp[1]]
            elif oldp[0] != newp[0]:
                diffs[acc_id] = [self.Tnt_amount_changed, newp[0], oldp[0]]
            elif oldp[1] != newp[1]:
                diffs[acc_id] = [self.Tnt_notes_changed, newp[1], oldp[1]]
        for acc_id, oldp in oldLines.items():
            newp = newLines.get(acc_id)
            if newp is None:
                diffs[acc_id] = [self.Tnt_transaction_removed]
            #elif oldp[0] != newp[0]:
            #    diffs[acc_id] = ... Tnt_amount_changed
            #elif oldp[1] != newp[1]:
            #    diffs[acc_id] = ... Tnt_notes_changed
        if modified_trans_id is not None and tdesc != old_desc:
            for acc_id in newLines:
                if acc_id not in diffs:
                    diffs[acc_id] = [self.Tnt_description_changed, tdesc, old_desc]
        if len(diffs) == 0:
            log_gassman.debug('nothing to notify for transaction %s modifying transaction %s',
                              trans_id, modified_trans_id)
            return
        # FIXME: soglia specifica di csa
        LVL_THRES = -40
        #signalledPeople = dict() # da persone (pid) a lista di account ([accountId])
        accounts = dict() # da account (accountId) a lista di persone ([{first/middle/last_name, email}])
        # considero solo gli account i cui owner hanno nei settaggi la ricezione di ogni notifica
        cur.execute(*self.application.conn.sql_factory.account_owners_with_optional_email_for_notifications(
            diffs.keys()
        ))
        for acc_id, pid, first_name, middle_name, last_name, email in cur.fetchall():
            #signalledPeople.setdefault(pid, []).append(acc_id)
            accounts.setdefault(
                acc_id,
                {}
            ).setdefault(
                'people',
                []
            ).append(dict(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                email=email
            ))
        if len(accounts) == 0:
            log_gassman.info('involved accounts has no mail to notify to')
            return
        cur.execute(*self.application.conn.sql_factory.account_total_for_notifications(accounts.keys()))
        for acc_id, total, curr_sym in cur.fetchall():
            accounts[acc_id]['account'] = (total, curr_sym)
        for acc_id, accData in accounts.items():
            total, curr_sym = accData['account']
            people = accData['people']
            notificationType = diffs[acc_id]
            receivers = [p['email'] for p in people if p['email']]
            if len(receivers) == 0:
                log_gassman.debug('transaction not notified, people do not have email account: people=%s, tid=%s',
                                  people, trans_id)
                continue
            cur.execute(*self.application.conn.sql_factory.person_notification_email(self.current_user))
            try:
                reply_to = cur.fetchone()[0]
            except:
                reply_to = None
            # TODO: Localizzazione del messaggio
            self.notify(
                'account_update',
                receivers=[p['email'] for p in people if p['email']],
                reply_to=reply_to,
                total=total,
                currency=curr_sym,
                threshold=LVL_THRES,
                people=people,
                tdesc=tdesc,
                tdate=tdate,
                dateFormatter=shortDate,
                accId=acc_id,
                transId=trans_id,
                modifiedTransId=modified_trans_id,
                old_desc=old_desc,
                notificationType=notificationType,
                publishedUrl=settings.PUBLISHED_URL,
                Tnt_new_transaction=self.Tnt_new_transaction,
                Tnt_amount_changed=self.Tnt_amount_changed,
                Tnt_notes_changed=self.Tnt_notes_changed,
                Tnt_transaction_removed=self.Tnt_transaction_removed,
                Tnt_description_changed=self.Tnt_description_changed,
            )
