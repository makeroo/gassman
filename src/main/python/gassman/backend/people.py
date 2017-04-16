from . import JsonBaseHandler, GDataException

import error_codes


class PeopleProfilesHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        pids = self.payload['pids']
        uid = self.current_user
        is_self = len(pids) == 1 and (pids[0] == 'me' or int(pids[0]) == uid)
        if is_self:
            if uid is None:
                raise GDataException(error_codes.E_not_authenticated, 401)
            pids = [uid]
        # if csa_id == 'null':
        #    if not is_self:
        #        raise GDataException(error_codes.E_permission_denied, 403)
        #    csa_id = None
        if not is_self and not self.application.is_member_of_csa(cur, uid, csa_id, False):
            raise GDataException(error_codes.E_permission_denied, 403)
        can_view_contacts = is_self or self.application.has_permission_by_csa(
            cur, self.application.conn.sql_factory.P_canViewContacts, uid, csa_id
        )
        r = {}
        if len(pids) == 0:
            return r

        def record(pid):
            p = r.get(pid, None)
            if p is None:
                p = {
                    'accounts': [],
                    'profile': None,
                    'permissions': [],
                    'contacts': []
                }
                r[pid] = p
            return p

        if csa_id == 'null':
            record(uid)
            # p['profile'] = self.application.find_person_by_id(uid)
        else:
            accs, perms, args = self.application.conn.sql_factory.people_profiles2(csa_id, pids)
            can_view_accounts = is_self or self.application.has_permission_by_csa(
                cur, self.application.conn.sql_factory.P_canCheckAccounts, uid, csa_id
            )
            cur.execute(accs, args)
            for acc in self.application.conn.sql_factory.iter_objects(cur):
                p = record(acc['person_id'])
                if can_view_accounts:
                    p['accounts'].append(acc)
            cur.execute(perms, args)
            for perm in self.application.conn.sql_factory.iter_objects(cur):
                p = record(perm['person_id'])
                if can_view_contacts:
                    p['permissions'].append(perm['perm_id'])
        if r.keys():
            profiles, contacts, args = self.application.conn.sql_factory.people_profiles1(r.keys())
            cur.execute(profiles, args)
            for prof in self.application.conn.sql_factory.iter_objects(cur):
                p = record(prof['id'])
                p['profile'] = prof
            if can_view_contacts:
                cur.execute(contacts, args)
                for addr in self.application.conn.sql_factory.iter_objects(cur):
                    p = record(addr['person_id'])
                    p['contacts'].append(addr)
            # TODO: indirizzi
        if is_self:
            cur.execute(*self.application.conn.sql_factory.find_user_csa(uid))
            p = record(uid)
            p['csa'] = {
                pid: {
                    'name': name,
                    'member': member
                } for pid, name, member in cur.fetchall()
                }
        return r


class PeopleNamesHandler (JsonBaseHandler):
    # FIXME: è una copia di AccountNames... cambiano permessi e c'è meno roba
    # come si risolve: si toglie da qua ogni riferimento ai conti (account_people_addresses)
    # da quella di sopra si toglie invece persone e contatti (rimane solo conti-persone)
    # lato js la parse prende questa e crea l'array contatti
    # e complete prende i conti e raggruppa
    def do(self, cur, csa_id):
        uid = self.current_user
        if not self.application.has_permission_by_csa(
                cur, self.application.conn.sql_factory.P_canManageShifts, uid, csa_id
        ):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.conn.sql_factory.account_people(csa_id))
        account_people = list(cur)
        cur.execute(*self.application.conn.sql_factory.account_people_addresses(csa_id))
        account_people_addresses = list(cur)
        return dict(
            people=account_people,
            addresses=account_people_addresses,
            )
