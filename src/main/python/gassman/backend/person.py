import logging

from . import JsonBaseHandler, GDataException

import error_codes


log_gassman = logging.getLogger('gassman.backend')


class PersonSaveHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        log_gassman.debug('saving: %s', p)
        profile = p['profile']
        pid = int(profile['id'])
        if csa_id == 'null':
            if pid != uid:
                raise GDataException(error_codes.E_permission_denied, 403)
            csa_id = None
        elif (
            not self.application.has_permission_by_csa(
                cur, self.application.conn.sql_factory.P_canEditContacts, uid, csa_id
            ) and
            uid != pid
        ):
            raise GDataException(error_codes.E_permission_denied, 403)
        # verifica che il delivery place appartenga al csa
        if csa_id is not None and profile['default_delivery_place_id'] is not None:
            cur.execute(*self.application.conn.sql_factory.csa_delivery_place_check(
                csa_id,
                profile['default_delivery_place_id']
            ))
            if cur.fetchone()[0] == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
        # salva profilo
        cur.execute(*self.application.conn.sql_factory.profile_update(profile))
        # salva contatti
        contacts = p['contacts']
        cur.execute(*self.application.conn.sql_factory.contacts_fetch(pid))
        ocontacts = [x[0] for x in cur.fetchall()]
        if ocontacts:
            cur.execute(*self.application.conn.sql_factory.contact_address_remove(ocontacts))
            cur.execute(*self.application.conn.sql_factory.person_contact_remove(ocontacts))
        saved_contacts = set()
        for c, i in zip(contacts, range(len(contacts))):
            naddress = c['address']
            nkind = c['kind']
            ncontact_type = c['contact_type']
            if not naddress:
                continue
            if nkind == self.application.conn.sql_factory.Ck_Id:
                continue
            if nkind not in self.application.conn.sql_factory.Ckk:
                continue
            saved_contact = (naddress, nkind, ncontact_type)
            if saved_contact in saved_contacts:
                continue
            saved_contacts.add(saved_contact)
            cur.execute(*self.application.conn.sql_factory.contact_address_insert(naddress, nkind, ncontact_type))
            aid = cur.lastrowid
            cur.execute(*self.application.conn.sql_factory.person_contact_insert(pid, aid, i))
        # salva permessi
        permissions = p.get('permissions')
        if permissions is not None and \
           csa_id is not None and \
           self.application.has_permission_by_csa(
               cur, self.application.conn.sql_factory.P_canGrantPermissions, uid, csa_id
           ):
            cur.execute(*self.application.conn.sql_factory.find_user_permissions(uid, csa_id))
            assignable_perms = set([row[0] for row in cur.fetchall()])
            cur.execute(*self.application.conn.sql_factory.permission_revoke(pid, csa_id, assignable_perms))
            for p in set(permissions) & assignable_perms:
                cur.execute(*self.application.conn.sql_factory.permission_grant(pid, p, csa_id))
        # TODO: salva indirizzi
        fee = p.get('membership_fee')
        if csa_id is not None and fee and self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canEditMembershipFee, uid, csa_id):
            # accId = fee.get('account')
            amount = fee.get('amount')
            if float(amount) >= 0:
                cur.execute(*self.application.conn.sql_factory.account_update_membership_fee(csa_id, pid, amount))


class PersonCheckEmailHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        log_gassman.debug('saving: %s', p)
        pid = p['id']
        email = p['email']
        if (
            not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canEditContacts, uid, csa_id) and
            uid != int(pid)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        # verifica unicità
        cur.execute(*self.application.conn.sql_factory.is_unique_email(pid, email))
        return cur.fetchone()[0]


class PersonSetFeeHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        if not self.application.has_permission_by_csa(
                cur, self.application.conn.sql_factory.P_canEditMembershipFee, uid, csa_id
        ):
            raise GDataException(error_codes.E_permission_denied, 403)
        person_id = int(p['pid'])
        fee = float(p['fee'])
        cur.execute(*self.application.conn.sql_factory.account_update_membership_fee(csa_id, person_id, fee))
