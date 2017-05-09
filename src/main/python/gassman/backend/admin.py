import datetime

from . import JsonBaseHandler, GDataException, rss_feed_id

import error_codes

from ..templateutils import member_name
from .transaction import insert_close_account_transaction

import gassman_settings as settings


class AdminPeopleIndexHandler (JsonBaseHandler):
    def do(self, cur, from_idx, to_idx):
        p = self.payload

        q = p.get('q')
        if q:
            q = '%%%s%%' % q
        o = self.application.conn.sql_factory.admin_people_index_order_by[int(self.payload.get('o', 0))]
        uid = self.current_user
        if self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canAdminPeople, uid, None):
            csa = p.get('csa')
            vck = p.get('vck', self.application.viewable_contact_kinds)
            cur.execute(*self.application.conn.sql_factory.admin_people_index(
                q,
                csa,
                o,
                int(from_idx),
                int(to_idx),
                vck,
            ))
        else:
            raise GDataException(error_codes.E_permission_denied)
        items = list(cur)
        if items:
            cur.execute(*self.application.conn.sql_factory.admin_count_people(q, csa, vck))
            count = cur.fetchone()[0]
        else:
            count = 0
        return {
            'items': items,
            'count': count
        }


class AdminPeopleProfilesHandler (JsonBaseHandler):
    def do(self, cur):
        pids = self.payload['pids']
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        r = {}
        if len(pids) == 0:
            return r
        profiles, contacts, args = self.application.conn.sql_factory.people_profiles1(pids)
        cur.execute(contacts, args)

        def record(p_id):
            return r.setdefault(
                p_id,
                {
                    'accounts': [],
                    'profile': None,
                    'permissions': [],
                    'contacts': []
                }
            )

        for acc in self.application.conn.sql_factory.iter_objects(cur):
            p = record(acc['person_id'])
            p['contacts'].append(acc)
        cur.execute(profiles, args)
        for prof in self.application.conn.sql_factory.iter_objects(cur):
            p = record(prof['id'])
            p['profile'] = prof
        for pid, p in r.items():
            cur.execute(*self.application.conn.sql_factory.find_user_csa(pid))
            p['csa'] = self.application.conn.sql_factory.iter_objects(cur)
        return r


class AdminPeopleRemoveHandler (JsonBaseHandler):
    def do(self, cur):
        pid = self.payload['pid']
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        # verifico che non abbia né abbia avuto conti
        cur.execute(*self.application.conn.sql_factory.find_user_csa(pid))
        if len(cur.fetchall()) > 0:
            raise GDataException(error_codes.E_cannot_remove_person_with_accounts)
        cur.execute(*self.application.conn.sql_factory.contact_address_delete(pid))
        cur.execute(*self.application.conn.sql_factory.contact_person_delete(pid))
        cur.execute(*self.application.conn.sql_factory.permission_revoke_all(pid))
        cur.execute(*self.application.conn.sql_factory.person_delete(pid))


class AdminPeopleJoinHandler (JsonBaseHandler):
    """
    Una stessa persona ha acceduto con un nuovo google account.

    Attualmente oldpid ha conti, permessi e un profilo, mentre newpid ha solo profilo.
    Ho complicato il merge all'inverosimile solo per permettere il merge furbo del profilo
    ma ho finito per gestire anche permessi e conti.
    Che una persona possa avere più conti, chiusi, in intervalli sovrapposti
    (intendo nello stesso CSA e con la stessa moneta) non ha molto senso. Ma se per
    quelli aperti è un vero e proprio vincolo imprescindibile, per i chiusi c'è un caso
    d'uso possibile: qualcuno che ha iniziato a usare la piattaforma, poi ha cambiato
    identità google, ha ripreso a usarla per poi voler recuperare le informazioni
    sulla vecchia. A dirlo, non ha molto senso, mi rendo conto...
    """
    def do(self, cur):
        newpid = self.payload['newpid']
        oldpid = self.payload['oldpid']

        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)

        def intersect(o1, o2):
            """
            So che o1.from_date <= o2.from_date e basta.
            :param o1: ownership
            :param o2: ownership
            :return: True se le ownerships si intersecano
            """
            o1t = o1['to_date']
            o2f = o2['from_date']
            o2t = o2['to_date']
            if o1t is None:
                return True
            if o2f > o1t:
                return False
            if o2t is None or o2t > o1t:
                o1['to_date'] = o2t
            return True

        # revisione e merge delle ownership di old e new
        cur.execute(*self.application.conn.sql_factory.person_accounts(newpid, oldpid))

        # da (csa_id, currency_id) -> [bool check]
        opens = {}
        # da (account_id) -> [account info]
        accounts = {}

        for acc_info in self.application.conn.sql_factory.iter_objects(cur):
            account_id = acc_info['id']
            accounts.setdefault(account_id, []).append(acc_info)

            t = acc_info['to_date']
            if t is None:
                csa = acc_info['csa_id']
                currency_id = acc_info['currency_id']
                check = opens.get((csa, currency_id), [False])
                if check[0]:
                    raise GDataException(error_codes.E_already_member)
                check[0] = True

        for ownerships in accounts.values():
            current_ownership = None
            ownerships_to_be_created = {}
            ownerships_to_be_deleted = set()

            for ownership in sorted(ownerships, key=lambda acc_info: acc_info['from_date']):
                if current_ownership is None:
                    current_ownership = ownership
                elif intersect(current_ownership, ownership):
                    ownerships_to_be_created[current_ownership['id']] = current_ownership['to_date']
                    ownerships_to_be_deleted.add(ownership['id'])
                else:
                    current_ownership = ownership

            if ownerships_to_be_deleted:
                q, a = self.application.conn.sql_factory.ownership_delete(ownerships_to_be_deleted)
                cur.execute(q, a)

            for ownership_id, to_date in ownerships_to_be_created:
                q, a = self.application.conn.sql_factory.ownership_change_to_date(ownership_id, to_date)
                cur.execute(q, a)

        # trasferisci le altre
        cur.execute(*self.application.conn.sql_factory.accounts_reassign(newpid, oldpid))

        # gestione contatti
        contacts_by_value = {}
        contacts_by_id = set()
        address_to_be_deleted = []
        pc_to_be_deleted = []
        cur.execute(*self.application.conn.sql_factory.contacts_fetch_all(newpid, oldpid))
        for pc_id, a_id, kind, contact_type, address in cur.fetchall():
            k = kind, contact_type, address
            if k in contacts_by_value:
                address_to_be_deleted.append(a_id)
                continue
            contacts_by_value[k] = (pc_id, a_id)
            if a_id in contacts_by_id:
                pc_to_be_deleted.append(pc_id)
                continue
            contacts_by_id.add(a_id)
        # cancello i duplicati per valore
        if address_to_be_deleted:
            cur.execute(*self.application.conn.sql_factory.person_contact_remove(address_to_be_deleted))
            cur.execute(*self.application.conn.sql_factory.contact_address_remove(address_to_be_deleted))
        # cancello le assegnazioni duplicate
        if pc_to_be_deleted:
            cur.execute(*self.application.conn.sql_factory.person_contact_remove_by_id(pc_to_be_deleted))

        cur.execute(*self.application.conn.sql_factory.contacts_reassign(newpid, oldpid))

        # gestione permessi
        granted_perms = set()
        grants_to_be_deleted = []
        cur.execute(*self.application.conn.sql_factory.permission_all(oldpid, newpid))
        for grant_id, csa_id, person_id, perm_id in cur.fetchall():
            k = (csa_id, perm_id)
            if k in granted_perms:
                grants_to_be_deleted.append(grant_id)
            else:
                granted_perms.add(k)
        # elimino duplicati
        if grants_to_be_deleted:
            cur.execute(*self.application.conn.sql_factory.permission_revoke_by_grant(grants_to_be_deleted))
        # riassegno i permessi
        cur.execute(*self.application.conn.sql_factory.permissions_reassign(newpid, oldpid))

        cur.execute(*self.application.conn.sql_factory.person_delete(oldpid))

        # Notifico, a tutte le email, l'avvenuto collegamento col preesistente account GassMan
        prof, contacts, args = self.application.conn.sql_factory.people_profiles1([newpid])
        cur.execute(prof, args)
        profile = self.application.conn.sql_factory.fetch_object(cur)
        contacts, args = self.application.conn.sql_factory.people_addresses([newpid], self.application.conn.sql_factory.Ck_Email)
        cur.execute(contacts, args)
        contacts = [row[1] for row in cur.fetchall()]
        self.notify(
            'joined_google_account',
            receivers=contacts,
            publishedUrl=settings.PUBLISHED_URL,
            profile=profile,
            contacts=contacts,
            member_name=member_name,
        )


class AdminPeopleAddHandler (JsonBaseHandler):
    """
    Cointesto conto.
    """
    def do(self, cur):
        csa = self.payload['csa']
        pid = self.payload['pid']
        mid = self.payload['mid']  # persona già membro
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        # chiudo conti precedenti
        now = datetime.datetime.utcnow()
        cur.execute(*self.application.conn.sql_factory.find_open_accounts(pid, csa))
        previous_accounts = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute(*self.application.conn.sql_factory.find_open_accounts(mid, csa))
        new_accounts = {row[0]: row[1] for row in cur.fetchall()}
        # nb: previous_accounts e new_accounts sono mappe da account id -> currency id
        # sono invertibili perché vale che ogni membro del gas ha un conto aperto per ogni
        # valuta gestita dal gas
        if not new_accounts:
            raise GDataException(error_codes.E_not_owner_or_already_closed)
        common_accounts = previous_accounts.keys() & new_accounts.keys()
        account_match = {}
        for previous_acc_id, curr_id in previous_accounts.items():
            if previous_acc_id in common_accounts:
                continue
            try:
                next_acc_id = [acc_id for acc_id, nc in new_accounts.items() if nc == curr_id][0]
            except IndexError:
                # MOLTO strano, ogni persona del gas ha un conto per ogni valuta
                # due errori possibili: o pid ha un conto con valuta non gestita dal gas
                # o mid non ha un conto con valuta gestita dal gas
                # non mi interessa distinguere, riporto pid, mid e valuta
                raise GDataException(error_codes.E_account_currency_mismatch, pid, mid, curr_id)
            account_match[previous_acc_id] = next_acc_id
        for previous_acc_id, next_acc_id in account_match.items():
            insert_close_account_transaction(
                cur,
                self.application.conn.sql_factory,
                previous_acc_id,
                now,
                'Cointestazione',  # TODO: i18n
                uid,
                next_acc_id
            )
            cur.execute(*self.application.conn.sql_factory.account_close(now, previous_acc_id, pid))
            cur.execute(*self.application.conn.sql_factory.account_grant(pid, next_acc_id, now))
        for next_acc_id in new_accounts:
            if next_acc_id in common_accounts:
                continue
            cur.execute(*self.application.conn.sql_factory.account_grant(pid, next_acc_id, now))
        # Notifico, a tutte le email di tutti gli intestatari, l'avvenuto collegamento col conto GASsMan.
        prof, contacts, args = self.application.conn.sql_factory.people_profiles1([pid, mid])
        cur.execute(prof, args)
        profiles = {x['id']: x for x in self.application.conn.sql_factory.iter_objects(cur)}
        contacts, args = self.application.conn.sql_factory.people_addresses([pid, mid], self.application.conn.sql_factory.Ck_Email)
        cur.execute(contacts, args)
        contacts = [row[1] for row in cur.fetchall()]
        self.notify(
            'joined_account',
            receivers=contacts,
            publishedUrl=settings.PUBLISHED_URL,
            newp=profiles[pid],
            memp=profiles[mid],
            contacts=contacts,
            previous_accounts=previous_accounts,
            new_accounts=new_accounts,
            common_accounts=common_accounts,
            member_name=member_name,
        )


class AdminPeopleCreateAccountHandler (JsonBaseHandler):
    """
    Creo un nuovo conto per un account GASsMan con associato un account Google.
    """
    def do(self, cur):
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        # TODO: errore se ha conti precedenti
        pid = self.payload['pid']
        csa = self.payload['csa']
        cur.execute(*self.application.conn.sql_factory.csa_currencies(csa))
        for row in cur.fetchall():
            curr = row[0]
            cur.execute(*self.application.conn.sql_factory.account_create(
                '%s' % pid,
                self.application.conn.sql_factory.At_Asset,
                csa,
                curr,
                0.0
            ))
            acc_id = cur.lastrowid
            cur.execute(*self.application.conn.sql_factory.account_grant(pid, acc_id, datetime.datetime.utcnow()))
        # TODO: notificare apertura conto


class AdminPeopleCreateHandler (JsonBaseHandler):
    """
    Creo un nuovo account GASsMan, per ora non agganciato ad un account Google.
    NB: non essendo agganciato ad un conto google non notifico niente.
    """
    def do(self, cur):
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, self.application.conn.sql_factory.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        first_name = self.payload['first_name']
        last_name = self.payload['last_name']
        csa = self.payload.get('csa')
        cur.execute(*self.application.conn.sql_factory.create_person(first_name, '', last_name))
        pid = cur.lastrowid
        rfi = rss_feed_id(pid)
        cur.execute(*self.application.conn.sql_factory.assign_rss_feed_id(pid, rfi))
        if csa is not None:
            cur.execute(*self.application.conn.sql_factory.csa_currencies(csa))
            acc = []
            for row in cur.fetchall():
                curr = row[0]
                cur.execute(*self.application.conn.sql_factory.account_create(
                    '%s %s' % (first_name, last_name),
                    self.application.conn.sql_factory.At_Asset,
                    csa,
                    curr,
                    0.0
                ))
                acc_id = cur.lastrowid
                cur.execute(*self.application.conn.sql_factory.account_grant(pid, acc_id, datetime.datetime.utcnow()))
                acc.append(acc_id)
        else:
            acc = None
        return {'pid': pid, 'acc': acc}


class PermissionGrantHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        perm_id = p['perm_id']
        if not self.application.has_permission_by_csa(
            cur, self.application.conn.sql_factory.P_canGrantPermissions, uid, csa_id
        ) or not self.application.has_permission_by_csa(
            cur, perm_id, uid, csa_id
        ):
            raise GDataException(error_codes.E_permission_denied, 403)
        person_id = p['person_id']
        q, a = self.application.conn.sql_factory.permission_grant(person_id, perm_id, csa_id)
        cur.execute(q, a)


class PermissionRevokeHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        perm_id = p['perm_id']
        if not self.application.has_permission_by_csa(
            cur, self.application.conn.sql_factory.P_canGrantPermissions, uid, csa_id
        ) or not self.application.has_permission_by_csa(
            cur, perm_id, uid, csa_id
        ):
            raise GDataException(error_codes.E_permission_denied, 403)
        person_id = p['person_id']
        q, a = self.application.conn.sql_factory.permission_revoke(person_id, csa_id, [perm_id])
        cur.execute(q, a)
