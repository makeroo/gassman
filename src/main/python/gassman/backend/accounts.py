from . import JsonBaseHandler, GDataException

import error_codes


class AccountsIndexHandler (JsonBaseHandler):
    def do(self, cur, csa_id, from_idx, to_idx):
        p = self.payload
        q = p.get('q')
        if q:
            q = '%%%s%%' % q
        dp = p['dp']
        ex = p.get('ex', False)
        o = self.application.conn.sql_factory.accounts_index_order_by[int(p['o'])]
        uid = self.current_user
        can_check_accounts = self.application.has_permission_by_csa(
            cur, self.application.conn.sql_factory.P_canCheckAccounts, uid, csa_id
        )
        can_view_contacts = self.application.has_permission_by_csa(
            cur, self.application.conn.sql_factory.P_canViewContacts, uid, csa_id
        )
        viewable_contacts = p.get('vck', self.application.viewable_contact_kinds) if can_view_contacts else None
        if can_check_accounts:
            cur.execute(*self.application.conn.sql_factory.accounts_index(csa_id, q, dp, o, ex, int(from_idx), int(to_idx), search_contact_kinds=viewable_contacts))
        elif can_view_contacts:
            cur.execute(*self.application.conn.sql_factory.people_index(csa_id, q, dp, o, ex, int(from_idx), int(to_idx), search_contact_kinds=viewable_contacts))
        else:
            raise GDataException(error_codes.E_permission_denied, 403)
        r = {
            'items': list(cur)
        }
        if len(r['items']):
            cur.execute(*self.application.conn.sql_factory.count_people(csa_id, q, dp, ex, search_contact_kinds=viewable_contacts))
            r['count'] = cur.fetchone()[0]
        else:
            r['count'] = 0
        return r


class AccountsNamesHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if not self.application.has_permissions(
                cur, self.application.conn.sql_factory.editableTransactionPermissions, uid, csa_id
        ):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.conn.sql_factory.account_currencies(csa_id))
        account_curs = list(cur)
        # cur.execute(*self.application.conn.sql_factory.account_people(csa_id))
        # account_people = list(cur)
        cur.execute(*self.application.conn.sql_factory.account_people_addresses(csa_id))
        account_people_addresses = list(cur)
        cur.execute(*self.application.conn.sql_factory.csa_account(
            csa_id, self.application.conn.sql_factory.At_Kitty, full=True
        ))
        kitty = {
            x['id']: x for x in self.application.conn.sql_factory.iter_objects(cur)
            }
        return dict(
            accountCurrencies=account_curs,
            # accountPeople=account_people,
            accountPeopleAddresses=account_people_addresses,
            kitty=kitty,
            )
