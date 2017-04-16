from . import JsonBaseHandler, GDataException

import error_codes


class TransactionsEditableHandler (JsonBaseHandler):
    def do(self, cur, csa_id, from_idx, to_idx):
        q = '%%%s%%' % self.payload['q']
        o = self.application.conn.sql_factory.transactions_editable_order_by[int(self.payload['o'])]
        uid = self.current_user
        if self.application.has_permission_by_csa(
                cur, self.application.conn.sql_factory.P_canManageTransactions, uid, csa_id
        ):
            cur.execute(*self.application.conn.sql_factory.transactions_all(csa_id, q, o, int(from_idx), int(to_idx)))
            q, a = self.application.conn.sql_factory.transactions_count_all(csa_id, q)
        elif self.application.has_permissions(
                cur, self.application.conn.sql_factory.editableTransactionPermissions, uid, csa_id
        ):
            cur.execute(*self.application.conn.sql_factory.transactions_by_editor(
                csa_id, uid, q, o, int(from_idx), int(to_idx)
            ))
            q, a = self.application.conn.sql_factory.transactions_count_by_editor(csa_id, uid, q)
        else:
            raise GDataException(error_codes.E_permission_denied, 403)
        r = {
            'items': list(cur.fetchall())
        }
        if len(r['items']):
            cur.execute(q, a)
            r['count'] = cur.fetchone()[0]
        else:
            r['count'] = 0
        return r
