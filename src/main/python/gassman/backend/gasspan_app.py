import sys
import logging
import datetime

import tornado.web
import tornado.gen

import loglib

from . import HomeHandler, Person, rss_feed_id
from .auth import GoogleAuthLoginHandler
from .sys import SysVersionHandler
from .account import AccountOwnerHandler, AccountMovementsHandler, AccountAmountHandler, AccountXlsHandler,\
    AccountCloseHandler
from .accounts import AccountsIndexHandler, AccountsNamesHandler
from .transaction import TransactionEditHandler, TransactionSaveHandler
from .transactions import TransactionsEditableHandler
from .csa import CsaInfoHandler, CsaUpdateHandler, CsaListHandler, CsaChargeMembershipFeeHandler,\
    CsaRequestMembershipHandler, CsaDeliveryPlacesHandler, CsaDeliveryDatesHandler, CsaAddShiftHandler,\
    CsaRemoveShiftHandler
from .rss import RssFeedHandler
from .people import PeopleProfilesHandler, PeopleNamesHandler
from .person import PersonSaveHandler, PersonCheckEmailHandler, PersonSetFeeHandler
from .event import EventSaveHandler, EventRemoveHandler
from .orders import OrdersOrderHandler
from .admin import AdminPeopleIndexHandler, AdminPeopleProfilesHandler, AdminPeopleRemoveHandler,\
    AdminPeopleJoinHandler, AdminPeopleAddHandler, AdminPeopleCreateAccountHandler, AdminPeopleCreateHandler,\
    PermissionGrantHandler, PermissionRevokeHandler

import gassman_settings as settings


log_gassman = logging.getLogger('gassman.backend')


class GassmanWebApp (tornado.web.Application):
    def __init__(self, conn, notify_service):
        handlers = [
            # (r'^/$', IndexHandler),
            (r'^/home.html$', HomeHandler),
            (r'^/gm/auth/google$', GoogleAuthLoginHandler),
            (r'^/gm/sys/version$', SysVersionHandler),
            (r'^/gm/account/(\d+)/owner$', AccountOwnerHandler),
            (r'^/gm/account/(\d+)/movements/(\d+)/(\d+)$', AccountMovementsHandler),
            (r'^/gm/account/(\d+)/amount$', AccountAmountHandler),
            (r'^/gm/account/(\d+)/xls$', AccountXlsHandler),
            (r'^/gm/account/(\d+)/close$', AccountCloseHandler),
            # (r'^/gm/profile-info$', ProfileInfoHandler),
            (r'^/gm/accounts/(\d+)/index/(\d+)/(\d+)$', AccountsIndexHandler),
            (r'^/gm/accounts/(\d+)/names$', AccountsNamesHandler),
            # (r'^/gm/expenses/(\d+)/tags$', ExpensesNamesHandler),
            (r'^/gm/transaction/(\d+)/(\d+)/edit$', TransactionEditHandler),
            (r'^/gm/transaction/(\d+)/save$', TransactionSaveHandler),
            (r'^/gm/transactions/(\d+)/editable/(\d+)/(\d+)$', TransactionsEditableHandler),
            (r'^/gm/csa/(\d+)/info$', CsaInfoHandler),
            (r'^/gm/csa/update$', CsaUpdateHandler),
            (r'^/gm/csa/list', CsaListHandler),
            (r'^/gm/csa/(\d+)/charge_membership_fee$', CsaChargeMembershipFeeHandler),
            (r'^/gm/csa/(\d+)/request_membership$', CsaRequestMembershipHandler),
            (r'^/gm/csa/(\d+)/delivery_places$', CsaDeliveryPlacesHandler),
            (r'^/gm/csa/(\d+)/delivery_dates$', CsaDeliveryDatesHandler),
            (r'^/gm/csa/(\d+)/add_shift', CsaAddShiftHandler),
            (r'^/gm/csa/(\d+)/remove_shift', CsaRemoveShiftHandler),
            # (r'^/gm/csa/(\d+)/total_amount$', CsaAmountHandler),
            (r'^/gm/rss/(.+)$', RssFeedHandler),
            (r'^/gm/people/(null|\d+)/profiles$', PeopleProfilesHandler),
            (r'^/gm/people/(\d+)/names$', PeopleNamesHandler),
            (r'^/gm/person/(null|\d+)/save$', PersonSaveHandler),
            (r'^/gm/person/(\d+)/check_email$', PersonCheckEmailHandler),
            (r'^/gm/person/(\d+)/set_fee', PersonSetFeeHandler),
            (r'^/gm/event/(\d+)/save$', EventSaveHandler),
            (r'^/gm/event/(\d+)/remove$', EventRemoveHandler),
            (r'^/gm/order$', OrdersOrderHandler),
            (r'^/gm/admin/people/index/(\d+)/(\d+)$', AdminPeopleIndexHandler),
            (r'^/gm/admin/people/profiles$', AdminPeopleProfilesHandler),
            (r'^/gm/admin/people/remove$', AdminPeopleRemoveHandler),
            (r'^/gm/admin/people/join$', AdminPeopleJoinHandler),
            (r'^/gm/admin/people/add$', AdminPeopleAddHandler),
            (r'^/gm/admin/people/create_account$', AdminPeopleCreateAccountHandler),
            (r'^/gm/admin/people/create$', AdminPeopleCreateHandler),
            (r'^/gm/permission/(\d+)/grant$', PermissionGrantHandler),
            (r'^/gm/permission/(\d+)/revoke$', PermissionRevokeHandler),
            ]
        # codeHome = os.path.dirname(__file__)
        sett = dict(
            cookie_secret=settings.COOKIE_SECRET,
            template_path=settings.TEMPLATE_PATH,  # os.path.join(codeHome, 'templates'),
            static_path=settings.STATIC_PATH,  # os.path.join(codeHome, "static"),
            xsrf_cookies=True,
            xsrf_cookie_version=1,
            # login_url = '/login.html',
            google_oauth={
                "key": settings.GOOGLE_OAUTH2_CLIENTID,
                "secret": settings.GOOGLE_OAUTH2_SECRET,
            },
            google_oauth_redirect=settings.GOOGLE_OAUTH2_REDIRECT,
            debug=settings.DEBUG_MODE,
            )
        super().__init__(handlers, **sett)
        self.conn = conn
        self.notify_service = notify_service
        self.viewable_contact_kinds = [
            self.conn.sql_factory.Ck_Telephone,
            self.conn.sql_factory.Ck_Mobile,
            self.conn.sql_factory.Ck_Email,
            self.conn.sql_factory.Ck_Fax,
            self.conn.sql_factory.Ck_Nickname,
        ]
        # self.sessions = dict()

    def has_or_had_account(self, cur, pid, acc_id):
        cur.execute(*self.conn.sql_factory.has_or_had_account(pid, acc_id))
        return cur.fetchone()[0] > 0

    def add_contact(self, cur, pid, addr, kind, notes):
        if addr:
            cur.execute(*self.conn.sql_factory.create_contact(addr, kind, notes))
            cid = cur.lastrowid
            cur.execute(*self.conn.sql_factory.assign_contact(cid, pid))

    @tornado.gen.coroutine
    def check_profile(self, request_handler, user):
        with self.conn.connection() as cur:
            auth_mode = (user.userId, user.authenticator, self.conn.sql_factory.Ck_Id)
            cur.execute(*self.conn.sql_factory.check_user(*auth_mode))
            pp = list(cur)
            if len(pp) == 0:
                log_gassman.debug('profile not found: credentials=%s', auth_mode)
                auth_mode = (user.email, 'verified', self.conn.sql_factory.Ck_Email)
                cur.execute(*self.conn.sql_factory.check_user(*auth_mode))
                pp = list(cur)
            if len(pp) == 0:
                log_gassman.info('profile not found: credentials=%s', auth_mode)
                p = None
            else:
                p = Person(*pp[0])
                if len(pp) == 1:
                    log_gassman.debug('found profile: credentials=%s, person=%s', auth_mode, p)
                if len(pp) > 1:
                    self.notify_service.notify(
                        '[ERROR] Multiple auth id for, check credentials: id=%s, cred=%s' % (p, auth_mode)
                    )
        try:
            yield user.load_full_profile()
            attrsToAdd = {
                self.conn.sql_factory.Ck_Email: (user.email, 'verified'),
                self.conn.sql_factory.Ck_Id: (user.userId, user.authenticator),
            }
            attrsToUpdate = {
                self.conn.sql_factory.Ck_GProfile: [user.gProfile, None, None],
                self.conn.sql_factory.Ck_Picture: [user.picture, None, None],
            }
            with self.conn.connection() as cur:
                if p is None:
                    cur.execute(*self.conn.sql_factory.create_person(user.firstName, user.middleName, user.lastName))
                    p_id = cur.lastrowid
                    rfi = rss_feed_id(p_id)
                    cur.execute(*self.conn.sql_factory.assign_rss_feed_id(p_id, rfi))
                    p = Person(p_id, user.firstName, user.middleName, user.lastName, rfi)
                    log_gassman.info('profile created: newUser=%s', p)
                else:
                    cur.execute(*self.conn.sql_factory.contacts_fetch_all(p.id))
                    for pc_id, a_id, kind, contact_type, addr in list(cur):
                        v = attrsToAdd.get(kind)
                        if v == (addr, contact_type):
                            attrsToAdd.pop(kind)
                            continue
                        v = attrsToUpdate.get(kind)
                        if v is None:
                            continue
                        elif v[0] == addr and v[1] == contact_type:
                            attrsToUpdate.pop(kind)
                        else:
                            v[2] = a_id
                # userId e email eventualmente li vado ad aggiungere
                # picture e gProfile invece li vado a sostituire
                for kind, (addr, ctype) in attrsToAdd.items():
                    self.add_contact(cur, p.id, addr, kind, ctype)
                for kind, (addr, ctype, addrPk) in attrsToUpdate.items():
                    if addrPk is None:
                        self.add_contact(cur, p.id, addr, kind, ctype)
                    else:
                        cur.execute(*self.conn.sql_factory.contact_address_update(addrPk, addr, ctype))
        except:
            etype, evalue, tb = sys.exc_info()
            log_gassman.error('profile creation failed: cause=%s/%s\nfull stacktrace:\n%s',
                              etype, evalue, loglib.TracebackFormatter(tb))
            self.notify_service.notify('[ERROR] User profile creation failed', 'Cause: %s/%s\nAuthId: %s (%s %s)\nTraceback:\n%s' %
                           (etype, evalue, user.userId, user.firstName, user.lastName, loglib.TracebackFormatter(tb))
                           )
        if p is not None:
            request_handler.set_secure_cookie("user", tornado.escape.json_encode(p.id))
            # qui registro chi si è autenticato
            cur.execute(*self.conn.sql_factory.update_last_login(p.id, datetime.datetime.utcnow()))
        return p

#    def session(self, request_handler):
#        xt = request_handler.xsrf_token
#        s = self.sessions.get(xt, None)
#        if s is None:
#            s = Session(self)
#            self.sessions[xt] = s
#        return s

    def check_membership_by_kitty(self, cur, person_id, acc_id):
        cur.execute(*self.conn.sql_factory.check_membership_by_kitty(person_id, acc_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('check membership by kitty: user=%s, acc=%s, r=%s', person_id, acc_id, r)
        return r

    def has_permission_by_account(self, cur, perm, person_id, acc_id):
        cur.execute(*self.conn.sql_factory.has_permission_by_account(perm, person_id, acc_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permission: user=%s, perm=%s, r=%s', person_id, perm, r)
        return r

    def is_member_of_csa(self, cur, person_id, csa_id, stillMember):
        cur.execute(*self.conn.sql_factory.is_user_member_of_csa(person_id, csa_id, stillMember))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('is member: user=%s, csa=%s, still=%s, r=%s', person_id, csa_id, stillMember, r)
        return r

    def has_permission_by_csa(self, cur, perm, person_id, csa_id):
        if perm is None:
            return False
        cur.execute(*self.conn.sql_factory.has_permission_by_csa(perm, person_id, csa_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permission: user=%s, perm=%s, r=%s', person_id, perm, r)
        return r

    def has_permissions(self, cur, perms, person_id, csa_id):
        cur.execute(*self.conn.sql_factory.has_permissions(perms, person_id, csa_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permissions: user=%s, perm=%s, r=%s', person_id, perms, r)
        return r

    def is_kitty_transition_and_is_member(self, cur, trans_id, person_id):
        cur.execute(*self.conn.sql_factory.transaction_on_kitty_and_user_is_member(trans_id, person_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('member can view kitty transation: user=%s, trans=%s, r=%s', person_id, trans_id, r)
        return r

    def is_transaction_editor(self, cur, trans_id, person_id):
        """
        Una transazione può essere creata/modificata da chi ha canEnterXX
        o da chi ha manageTrans.
        Per verificare devo risalire la catena delle sovrascritture.
        """
        while trans_id is not None:
            cur.execute(*self.conn.sql_factory.log_transaction_check_operator(person_id, trans_id))
            if cur.fetchone()[0] > 0:
                return True
            cur.execute(*self.conn.sql_factory.transaction_previuos(trans_id))
            l = cur.fetchone()
            trans_id = l[0] if l is not None else None
        return False

    def isInvolvedInTransaction(self, cur, trans_id, person_id):
        while trans_id is not None:
            cur.execute(*self.conn.sql_factory.transaction_is_involved(trans_id, person_id))
            if cur.fetchone()[0] > 0:
                return True
            cur.execute(*self.conn.sql_factory.transaction_previuos(trans_id))
            l = cur.fetchone()
            trans_id = l[0] if l is not None else None
        return False
