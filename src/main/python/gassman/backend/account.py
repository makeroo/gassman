import logging
import datetime
import xlwt

from tornado.web import HTTPError

from . import BaseHandler, JsonBaseHandler, GDataException
from .transaction import insert_close_account_transaction

import error_codes


log_gassman = logging.getLogger('gassman.backend')


class AccountOwnerHandler (JsonBaseHandler):
    def do(self, cur, acc_id):
        uid = self.current_user
        if (not self.application.has_or_had_account(cur, uid, acc_id) and
            not self.application.has_permission_by_account(
                cur,
                self.application.conn.sql_factory.P_canCheckAccounts, uid, acc_id
            ) and
            not self.application.check_membership_by_kitty(cur, uid, acc_id)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.conn.sql_factory.account_owners(acc_id))
        oo = list(cur)
        if oo:
            return dict(people=oo)
        # se il conto non è di una persona, sarà del csa
        cur.execute(*self.application.conn.sql_factory.account_description(acc_id))
        return dict(desc=cur.fetchone())


class AccountMovementsHandler (JsonBaseHandler):
    def do(self, cur, acc_id, from_idx, to_idx):
        uid = self.current_user
        if (not self.application.has_or_had_account(cur, uid, acc_id) and
            not self.application.has_permission_by_account(cur, self.application.conn.sql_factory.P_canCheckAccounts, uid, acc_id) and
            not self.application.check_membership_by_kitty(cur, uid, acc_id)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        p = self.payload
        f = p.get('filter')
        if f:
            f = '%%%s%%' % f
        cur.execute(*self.application.conn.sql_factory.account_movements(acc_id, f, int(from_idx), int(to_idx)))
        r = {
            'items': list(cur.fetchall())
        }
        cur.execute(*self.application.conn.sql_factory.count_account_movements(acc_id, f))
        r['count'] = cur.fetchone()[0]
        return r


class AccountAmountHandler (JsonBaseHandler):
    def do(self, cur, acc_id):
        uid = self.current_user
        if (not self.application.has_or_had_account(cur, uid, acc_id) and
            not self.application.has_permission_by_account(cur, self.application.conn.sql_factory.P_canCheckAccounts, uid, acc_id) and
            not self.application.check_membership_by_kitty(cur, uid, acc_id)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.conn.sql_factory.account_amount(acc_id))
        v = cur.fetchone()
        return v[0] or 0.0, v[1]


class AccountXlsHandler (BaseHandler):
    def get(self, acc_id):
        uid = self.current_user
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/vnd.ms-excel')
        self.clear_header('Content-Disposition')
        self.add_header('Content-Disposition', 'attachment; filename="account-%s.xls"' % acc_id)
        with self.application.conn.connection() as cur:
            if (not self.application.has_or_had_account(cur, uid, acc_id) and
                not self.application.has_permission_by_account(
                    cur, self.application.conn.sql_factory.P_canCheckAccounts, uid, acc_id
                ) and
                not self.application.check_membership_by_kitty(cur, uid, acc_id)
                ):
                raise HTTPError(403)
            style = xlwt.XFStyle()
            style.num_format_str = 'YYYY-MM-DD'  # FIXME: i18n
            w = xlwt.Workbook(encoding='utf-8')
            s = w.add_sheet('Conto')  # FIXME: correggere e i18n
            cur.execute(*self.application.conn.sql_factory.account_movements(acc_id, None, None, None))
            # t.description, t.transaction_date, l.description, l.amount, t.id, c.symbol, t.cc_type
            row = 1
            tdescmaxlength = 0
            ldescmaxlength = 0
            s.write(0, 0, "Data")  # FIXME: i18n
            s.write(0, 1, "#")
            s.write(0, 2, "Ammontare")
            s.write(0, 3, "Valuta")
            s.write(0, 4, "Descrizione")
            s.write(0, 5, "Note")
            for tdesc, tdate, ldesc, lamount, tid, csym, _tcctype in cur.fetchall():
                s.write(row, 0, tdate, style)
                s.write(row, 1, tid)
                s.write(row, 2, lamount)
                s.write(row, 3, csym)
                if tdesc:
                    s.write(row, 4, tdesc)
                    if len(tdesc) > tdescmaxlength:
                        tdescmaxlength = len(tdesc)
                if ldesc:
                    s.write(row, 5, ldesc)
                    if len(ldesc) > ldescmaxlength:
                        ldescmaxlength = len(ldesc)
                row += 1
            if tdescmaxlength:
                s.col(4).width = 256 * tdescmaxlength
            if ldescmaxlength:
                s.col(4).width = 256 * ldescmaxlength
            w.save(self)
            self.finish()


class AccountCloseHandler (JsonBaseHandler):
    def do(self, cur, acc_id):
        uid = self.current_user
        p = self.payload
        if not self.application.has_permission_by_account(
                cur, self.application.conn.sql_factory.P_canCloseAccounts, uid, acc_id
        ):
            raise GDataException(error_codes.E_permission_denied, 403)
        # marca chiuso
        now = datetime.datetime.utcnow()
        owner_id = p['owner']
        tdesc = p.get('tdesc', '')
        cur.execute(*self.application.conn.sql_factory.account_close(now, acc_id, owner_id))
        affected_rows = cur.rowcount
        if affected_rows == 0:
            log_gassman.warning('not owner, can\'t close account: account=%s, owner=%s', acc_id, owner_id)
            return {'error': error_codes.E_not_owner_or_already_closed}
        if affected_rows > 1:
            log_gassman.error('multiple account assignments: account=%s, owner=%s, rows=%s',
                              acc_id, owner_id, affected_rows)
        # calcola saldo
        cur.execute(*self.application.conn.sql_factory.account_has_open_owners(acc_id))
        if cur.fetchone() is not None:
            log_gassman.info('account still in use, no need for a "z" transaction: account=%s', acc_id)
            return {
                'info': error_codes.I_account_open
            }
        else:
            tid = insert_close_account_transaction(
                cur,
                self.application.conn.sql_factory,
                acc_id,
                now,
                tdesc,
                uid,
                None
            )

            if tid is None:
                log_gassman.info('closed account was empty, no "z" transaction needed: account=%s')
                return {
                    'info': error_codes.I_empty_account
                }
            else:
                return {
                    'tid': tid
                }
