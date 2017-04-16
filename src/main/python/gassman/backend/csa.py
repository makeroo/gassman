import datetime

from . import JsonBaseHandler, GDataException

import error_codes


class CsaInfoHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if not self.application.is_member_of_csa(cur, uid, csa_id, False):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.conn.sql_factory.csa_info(csa_id))
        r = self.application.conn.sql_factory.fetch_object(cur)
        cur.execute(*self.application.conn.sql_factory.csa_account(
            csa_id, self.application.conn.sql_factory.At_Kitty, full=True
        ))
        r['kitty'] = self.application.conn.sql_factory.fetch_object(cur)  # FIXME: più di uno!
        cur.execute(*self.application.conn.sql_factory.csa_last_kitty_deposit(r['kitty']['id']))
        r['last_kitty_deposit'] = self.application.conn.sql_factory.fetch_object(cur)
        return r


class CsaUpdateHandler (JsonBaseHandler):
    def do(self, cur):
        uid = self.current_user
        csa = self.payload
        if not self.application.has_permission_by_csa(
                cur, self.application.conn.sql_factory.P_csaEditor, uid, csa['id']
        ):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.conn.sql_factory.csa_update(csa))


class CsaListHandler (JsonBaseHandler):
    def do(self, cur):
        uid = self.current_user
        cur.execute(*self.application.conn.sql_factory.csa_list(uid))
        return self.application.conn.sql_factory.iter_objects(cur)


class CsaChargeMembershipFeeHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if not self.application.has_permission_by_csa(
                cur, self.application.conn.sql_factory.P_canEditMembershipFee, uid, csa_id
        ):
            raise GDataException(error_codes.E_permission_denied, 403)

        p = self.payload
        t_desc = p.get('description', '')
        amount = p['amount']
        kitty_id = p['kitty']
        if amount < 0:
            raise GDataException(error_codes.E_illegal_amount)
        now = datetime.datetime.utcnow()
        cur.execute(*self.application.conn.sql_factory.csa_account(
            csa_id, self.application.conn.sql_factory.At_Kitty, acc_id=kitty_id, full=True
        ))
        acc = self.application.conn.sql_factory.fetch_object(cur)
        if acc is None:
            raise GDataException(error_codes.E_illegal_kitty)
        currency_id = acc['currency_id']
        cur.execute(*self.application.conn.sql_factory.insert_transaction(
            t_desc,
            now,
            self.application.conn.sql_factory.Tt_MembershipFee,
            currency_id,
            csa_id
        ))
        tid = cur.lastrowid
        cur.execute(*self.application.conn.sql_factory.insert_transaction_line_membership_fee(
            tid, amount, csa_id, currency_id
        ))

        cur.execute(*self.application.conn.sql_factory.insert_transaction_line(tid, '', +1, kitty_id))
        last_line_id = cur.lastrowid
        cur.execute(*self.application.conn.sql_factory.transaction_calc_last_line_amount(tid, last_line_id))
        a = cur.fetchone()[0]
        # involvedAccounts[lastAccId] = str(a)
        cur.execute(*self.application.conn.sql_factory.transaction_fix_amount(last_line_id, a))

        cur.execute(*self.application.conn.sql_factory.log_transaction(
            tid,
            uid,
            self.application.conn.sql_factory.Tl_Added,
            self.application.conn.sql_factory.Tn_kitty_deposit,
            now
        ))
        return {'tid': tid}


class CsaRequestMembershipHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if self.application.is_member_of_csa(cur, uid, csa_id, True):
            raise GDataException(error_codes.E_already_member)
        profiles, contacts, args = self.application.conn.sql_factory.people_profiles1([uid])
        cur.execute(profiles, args)
        profile = self.application.conn.sql_factory.fetch_object(cur)
        cur.execute(contacts, args)
        contacts = list(self.application.conn.sql_factory.iter_objects(cur))

        self.notify(
            'membership_request',
            profile=profile,
            contacts=contacts
        )


class CsaDeliveryPlacesHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if not self.application.is_member_of_csa(cur, uid, csa_id, True):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.conn.sql_factory.csa_delivery_places(csa_id))
        return self.application.conn.sql_factory.iter_objects(cur)


class CsaDeliveryDatesHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        if not self.application.is_member_of_csa(cur, uid, csa_id, True):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.conn.sql_factory.csa_delivery_dates(
            csa_id,
            p['from'],
            p['to'],
            [dp_id for dp_id, enabled in p.get('delivery_places', {}).items() if enabled]
        ))
        delivery_dates = self.application.conn.sql_factory.iter_objects(cur)
        wprofiles = {}
        if len(delivery_dates):
            # cur.execute(*self.application.conn.sql_factory.csa_delivery_shifts(set([ s['id'] for s in r ])))
            # for s in self.application.conn.sql_factory.iter_objects(cur):
            #    d = s['delivery_date_id']
            #
            workers = set()
            for s in delivery_dates:
                cur.execute(*self.application.conn.sql_factory.csa_delivery_shifts(s['id']))
                s['shifts'] = self.application.conn.sql_factory.iter_objects(cur)
                workers.update([w['person_id'] for w in s['shifts']])
            if workers:
                profiles, contacts, args = self.application.conn.sql_factory.people_profiles1(workers)
                cur.execute(profiles, args)

                def record(pid):
                    u = wprofiles.get(pid, None)
                    if u is None:
                        u = {
                            'accounts': [],
                            'profile': None,
                            'permissions': [],
                            'contacts': []
                        }
                        wprofiles[pid] = u
                    return u

                for prof in self.application.conn.sql_factory.iter_objects(cur):
                    p = record(prof['id'])
                    p['profile'] = prof
                cur.execute(contacts, args)
                for addr in self.application.conn.sql_factory.iter_objects(cur):
                    p = record(addr['person_id'])
                    p['contacts'].append(addr)
                # TODO: indirizzi
        return {
            'delivery_dates': delivery_dates,
            'profiles': wprofiles,
        }


class CsaAddShiftHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        if not self.application.is_member_of_csa(cur, uid, csa_id, True):
            raise GDataException(error_codes.E_permission_denied, 403)

        if uid != p['person_id'] and \
           not self.application.has_permission_by_csa(
               cur, self.application.conn.sql_factory.P_canManageShifts, uid, csa_id
           ):
            raise GDataException(error_codes.E_permission_denied, 403)

        delivery_date_id = p['delivery_date_id']
        shift_id = p['id']
        if shift_id is None:
            cur.execute(*self.application.conn.sql_factory.csa_delivery_date_check(csa_id, delivery_date_id))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
            cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_add(p))
            return {'id': cur.lastrowid}
        else:
            cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_check(csa_id, shift_id))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
            cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_update(shift_id, p['role']))


class CsaRemoveShiftHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload

        shift_id = p['id']
        if self.application.has_permission_by_csa(
                cur, self.application.conn.sql_factory.P_canManageShifts, uid, csa_id
        ):
            cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_check(csa_id, shift_id))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
        else:
            cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_check(csa_id, shift_id, uid))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)

        cur.execute(*self.application.conn.sql_factory.csa_delivery_shift_remove(shift_id))
