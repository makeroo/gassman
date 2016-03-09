#!/usr/bin/env python3

"""
Created on 01/mar/2014

@author: makeroo
"""

import datetime
import hashlib
import logging.config
import sys
import json

import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.gen
import tornado.httpclient
import tornado.escape

import xlwt

import gassman_settings as settings
import oauth2lib
from tornado.web import HTTPError

logging.config.dictConfig(settings.LOG)

import jsonlib
import pymysql
import loglib

import gassman_version
import sql
import error_codes


log_gassman = logging.getLogger('gassman.application')
log_gassman_db = logging.getLogger('gassman.application.db')


def rss_feed_id(pid):
    return hashlib.sha256((settings.COOKIE_SECRET + str(pid)).encode('utf-8')).hexdigest()


class GDataException (Exception):
    pass


class GoogleUser (object):
    authenticator = 'Google2'

    def __init__(self, id_token):
        oauth2token = oauth2lib.extract_payload_from_oauth2_id_token(id_token['id_token'])
        self.userId = oauth2token['sub']
        self.email = oauth2token['email']
        self.access_token = id_token['access_token']

    @tornado.gen.coroutine
    def loadFullProfile(self):
        http = tornado.httpclient.AsyncHTTPClient()
        response = yield http.fetch('https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token=' + self.access_token,
                                   method="GET")
        if response.error:
            raise Exception('Google auth error: %s' % str(response))

        profile = tornado.escape.json_decode(response.body)
        self.firstName = profile.get('given_name')
        self.middleName =  None
        self.lastName = profile.get('family_name')
        self.gProfile = profile.get('link')
        self.picture = profile.get('picture')
        # altri attributi: id, email, gender, locale


# class Session (object):
#    def __init__ (self, app):
#        self.application = app
#        self.created = datetime.datetime.utcnow()
#        self.registrationNotificationSent = False


class Person (object):
    class DoesNotExist (Exception):
        pass

    def __init__(self, p_id, p_first_name, p_middle_name, p_last_name, p_rss_feed_id):
        self.id = p_id
        self.firstName = p_first_name
        self.middleName = p_middle_name
        self.lastName = p_last_name
        #self.account = p_current_account_id
        self.rssFeedId = p_rss_feed_id

    def __str__(self):
        return '%s (%s %s)' % (self.id, self.firstName, self.lastName)


class GassmanWebApp (tornado.web.Application):
    def __init__ (self, sql, mailer, connArgs):
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
            (r'^/gm/person/(null|\d+)/save$', PersonSaveHandler),
            (r'^/gm/person/(\d+)/check_email$', PersonCheckEmailHandler),
            (r'^/gm/event/(\d+)/save$', EventSaveHandler),
            (r'^/gm/event/(\d+)/remove$', EventRemoveHandler),
            (r'^/gm/admin/people/index/(\d+)/(\d+)$', AdminPeopleIndexHandler),
            (r'^/gm/admin/people/profiles$', AdminPeopleProfilesHandler),
            (r'^/gm/admin/people/remove', AdminPeopleRemoveHandler),
            (r'^/gm/admin/people/join', AdminPeopleJoinHandler),
            (r'^/gm/admin/people/add', AdminPeopleAddHandler),
            (r'^/gm/admin/people/create_account', AdminPeopleCreateAccountHandler),
            (r'^/gm/admin/people/create', AdminPeopleCreateHandler),
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
        self.mailer = mailer
        self.connArgs = connArgs
        self.conn = None
        self.sql = sql
        self.viewable_contact_kinds = [
            self.sql.Ck_Telephone,
            self.sql.Ck_Mobile,
            self.sql.Ck_Email,
            self.sql.Ck_Fax,
            self.sql.Ck_Nickname,
        ]

        # self.sessions = dict()
        self.connect()
        tornado.ioloop.PeriodicCallback(self.check_conn, settings.DB_CHECK_INTERVAL).start()

    def connect(self):
        if self.conn is not None:
            try:
                self.conn.close()
                self.conn = None
            except:
                pass
        self.conn = pymysql.connect(**self.connArgs)

    def check_conn(self):
        try:
            try:
                with self.conn as cur:
                    cur.execute(self.sql.checkConn())
                    list(cur)
            except pymysql.err.OperationalError as e:
                if e.args[0] == 2013:
                    # pymysql.err.OperationalError: (2013, 'Lost connection to MySQL server during query')
                    # provo a riconnettermi
                    log_gassman.warning('mysql closed connection, reconnecting')
                    self.connect()
                else:
                    raise
        except:
            etype, evalue, tb = sys.exc_info()
            log_gassman.fatal('db connection failed: cause=%s/%s', etype, evalue)
            self.notify('[FATAL] No db connection', 'Connection error: %s/%s.\nTraceback:\n%s' %
                           (etype, evalue, loglib.TracebackFormatter(tb))
                           )

    def notify(self, subject, body, receivers = None, replyTo=None):
        if self.mailer is None:
            log_gassman.info('SMTP not configured, mail not sent: dest=%s, subj=%s\n%s', receivers, subject, body)
        else:
            self.mailer.send(settings.SMTP_SENDER,
                             receivers or settings.SMTP_RECEIVER,
                             '[GASsMan] %s' % subject,
                             body,
                             replyTo
                             )

    # def find_person_by_id (self, pid):
    #    with self.conn as cur:
    #        cur.execute(*self.sql.find_person(pid))
    #        pdata = cur.fetchone()
    #        if pdata:
    #            return Person(*pdata)
    #    return None

    def has_or_had_account(self, cur, pid, acc_id):
        cur.execute(*self.sql.has_or_had_account(pid, acc_id))
        return cur.fetchone()[0] > 0

    def add_contact(self, cur, pid, addr, kind, notes):
        if addr:
            cur.execute(*self.sql.create_contact(addr, kind, notes))
            cid = cur.lastrowid
            cur.execute(*self.sql.assign_contact(cid, pid))

    @tornado.gen.coroutine
    def check_profile(self, requestHandler, user):
        with self.conn as cur:
            authMode = (user.userId, user.authenticator, self.sql.Ck_Id)
            cur.execute(*self.sql.check_user(*authMode))
            pp = list(cur)
            if len(pp) == 0:
                log_gassman.debug('profile not found: credentials=%s', authMode)
                authMode = (user.email, 'verified', self.sql.Ck_Email)
                cur.execute(*self.sql.check_user(*authMode))
                pp = list(cur)
            if len(pp) == 0:
                log_gassman.info('profile not found: credentials=%s', authMode)
                p = None
            else:
                p = Person(*pp[0])
                if len(pp) == 1:
                    log_gassman.debug('found profile: credentials=%s, person=%s', authMode, p)
                if len(pp) > 1:
                    self.notify('[ERROR] Multiple auth id for %s' % p, 'Check credentials %s' % authMode)
        try:
            yield user.loadFullProfile()
            attrsToAdd = {
                self.sql.Ck_Email: (user.email, 'verified'),
                self.sql.Ck_Id: (user.userId, user.authenticator),
            }
            attrsToUpdate = {
                self.sql.Ck_GProfile: [user.gProfile, None, None],
                self.sql.Ck_Picture: [user.picture, None, None],
            }
            with self.conn as cur:
                if p is None:
                    cur.execute(*self.sql.create_person(user.firstName, user.middleName, user.lastName))
                    p_id = cur.lastrowid
                    rfi = rss_feed_id(p_id)
                    cur.execute(*self.sql.assign_rss_feed_id(p_id, rfi))
                    p = Person(p_id, user.firstName, user.middleName, user.lastName, rfi)
                    log_gassman.info('profile created: newUser=%s', p)
                else:
                    cur.execute(*self.sql.fetchAllContacts(p.id))
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
                        cur.execute(*self.sql.updateAddress(addrPk, addr, ctype))
        except:
            etype, evalue, tb = sys.exc_info()
            log_gassman.error('profile creation failed: cause=%s/%s\nfull stacktrace:\n%s', etype, evalue, loglib.TracebackFormatter(tb))
            self.notify('[ERROR] User profile creation failed', 'Cause: %s/%s\nAuthId: %s (%s %s)\nTraceback:\n%s' %
                           (etype, evalue, user.userId, user.firstName, user.lastName, loglib.TracebackFormatter(tb))
                           )
        if p is not None:
            requestHandler.set_secure_cookie("user", tornado.escape.json_encode(p.id))
            # qui registro chi si è autenticato
            cur.execute(*self.sql.update_last_login(p.id, datetime.datetime.utcnow()))
        return p

#    def session(self, requestHandler):
#        xt = requestHandler.xsrf_token
#        s = self.sessions.get(xt, None)
#        if s is None:
#            s = Session(self)
#            self.sessions[xt] = s
#        return s

    def check_membership_by_kitty(self, cur, person_id, acc_id):
        cur.execute(*self.sql.check_membership_by_kitty(person_id, acc_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('check membership by kitty: user=%s, acc=%s, r=%s', person_id, acc_id, r)
        return r

    def has_permission_by_account(self, cur, perm, person_id, acc_id):
        cur.execute(*self.sql.has_permission_by_account(perm, person_id, acc_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permission: user=%s, perm=%s, r=%s', person_id, perm, r)
        return r

    def is_member_of_csa(self, cur, person_id, csa_id, stillMember):
        cur.execute(*self.sql.is_user_member_of_csa(person_id, csa_id, stillMember))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('is member: user=%s, csa=%s, still=%s, r=%s', person_id, csa_id, stillMember, r)
        return r

    def has_permission_by_csa(self, cur, perm, person_id, csa_id):
        if perm is None:
            return False
        cur.execute(*self.sql.has_permission_by_csa(perm, person_id, csa_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permission: user=%s, perm=%s, r=%s', person_id, perm, r)
        return r

    def has_permissions(self, cur, perms, person_id, csa_id):
        cur.execute(*self.sql.has_permissions(perms, person_id, csa_id))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permissions: user=%s, perm=%s, r=%s', person_id, perms, r)
        return r

    def is_kitty_transition_and_is_member(self, cur, trans_id, person_id):
        cur.execute(*self.sql.transaction_on_kitty_and_user_is_member(trans_id, person_id))
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
            cur.execute(*self.sql.log_transaction_check_operator(person_id, trans_id))
            if cur.fetchone()[0] > 0:
                return True
            cur.execute(*self.sql.transaction_previuos(trans_id))
            l = cur.fetchone()
            trans_id = l[0] if l is not None else None
        return False

    def isInvolvedInTransaction(self, cur, trans_id, person_id):
        while trans_id is not None:
            cur.execute(*self.sql.transaction_is_involved(trans_id, person_id))
            if cur.fetchone()[0] > 0:
                return True
            cur.execute(*self.sql.transaction_previuos(trans_id))
            l = cur.fetchone()
            trans_id = l[0] if l is not None else None
        return False


class BaseHandler (tornado.web.RequestHandler):
    def get_current_user(self):
        c = self.get_secure_cookie('user', max_age_days=settings.COOKIE_MAX_AGE_DAYS)
        return int(c) if c else None

    def notify(self, template, receivers=None, replyTo=None, **namespace):
        subject = self.render_string(
            "%s.subject.email" % template,
            **namespace
        )
        body = self.render_string(
            "%s.body.email" % template,
            **namespace
        )
        self.application.notify(
            subject.decode('UTF-8'),
            body.decode('UTF-8'),
            receivers,
            replyTo
        )


class GoogleAuthLoginHandler (tornado.web.RequestHandler, tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            id_token = yield self.get_authenticated_user(
                redirect_uri=self.settings['google_oauth_redirect'],
                code=self.get_argument('code')
                )
            token_user = GoogleUser(id_token)
            # check_profile ritorna person ma a me interessa solo la registrazione su db
            yield self.application.check_profile(self, token_user)
            self.redirect("/home.html")
        else:
            yield self.authorize_redirect(
                redirect_uri=self.settings['google_oauth_redirect'],
                client_id=self.settings['google_oauth']['key'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})


# TODO: facebook login


# TODO: twitter login


class HomeHandler (BaseHandler):
    def get(self):
        u = self.current_user
        if u is not None:
            with self.application.conn as cur:
                cur.execute(*self.application.sql.update_last_visit(u, datetime.datetime.utcnow()))
        self.xsrf_token  # leggere il cookie => generarlo
        self.render(
            'home.html',
            LOCALE=self.locale.code,
        )


class JsonBaseHandler (BaseHandler):
    notifyExceptions = False

    def post(self, *args):
        with self.application.conn as cur:
            m = cur.execute

            def logging_execute(sql, *args):
                stmt = sql.upper().strip()
                logm = log_gassman_db.debug if stmt.startswith('SELECT') else log_gassman_db.info
                logm('SQL: %s / %s', sql, args)
                m(sql, *args)

            cur.execute = logging_execute
            r = self.do(cur, *args)
            self.write_response(r)

    def write_response(self, data):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        jsonlib.write_json(data, self)

    def write_error(self, status_code, **kwargs):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        etype, evalue, tb = kwargs.get('exc_info', ('', '', None))
        if self.notifyExceptions:
            self.application.notify(
                '[ERROR] Json API Failed',
                'Request error:\ncause=%s/%s\nother args: %s\nTraceback:\n%s' %
                (etype, evalue, kwargs, loglib.TracebackFormatter(tb))
            )
        if etype == GDataException:
            args = evalue.args
            i = [args[0]]
            self.set_status(args[1] if len(args) > 1 else 400)
        elif hasattr(evalue, 'args'):
            i = [str(etype)] + [str(x) for x in evalue.args]
        else:
            i = [str(etype), str(evalue)]
        # tanto logga tornado
        # log_gassman.error('unexpected exception: %s/%s', etype, evalue)
        # log_gassman.debug('full stacktrace:\n', loglib.TracebackFormatter(tb))
        jsonlib.write_json(i, self)

    @property
    def payload(self):
        if not hasattr(self, '_payload'):
            try:
                x = self.request.body
                s = x.decode('utf8')
                self._payload = json.loads(s)
            except:
                etype, evalue, tb = sys.exc_info()
                log_gassman.error('illegal payload: cause=%s/%s', etype, evalue)
                log_gassman.debug('full stacktrace:\n%s', loglib.TracebackFormatter(tb))
                raise GDataException(error_codes.E_illegal_payload)
        return self._payload


class SysVersionHandler (JsonBaseHandler):
    def post(self):
        data = [gassman_version.version]
        self.write_response(data)


class AccountOwnerHandler (JsonBaseHandler):
    def do(self, cur, acc_id):
        uid = self.current_user
        if (not self.application.has_or_had_account(cur, uid, acc_id) and
            not self.application.has_permission_by_account(cur, self.application.sql.P_canCheckAccounts, uid, acc_id) and
            not self.application.check_membership_by_kitty(cur, uid, acc_id)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.sql.account_owners(acc_id))
        oo = list(cur)
        if oo:
            return dict(people=oo)
        # se il conto non è di una persona, sarà del csa
        cur.execute(*self.application.sql.account_description(acc_id))
        return dict(desc=cur.fetchone())


class AccountMovementsHandler (JsonBaseHandler):
    def do(self, cur, acc_id, from_idx, to_idx):
        uid = self.current_user
        if (not self.application.has_or_had_account(cur, uid, acc_id) and
            not self.application.has_permission_by_account(cur, self.application.sql.P_canCheckAccounts, uid, acc_id) and
            not self.application.check_membership_by_kitty(cur, uid, acc_id)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        p = self.payload
        f = p.get('filter')
        if f:
            f = '%%%s%%' % f
        cur.execute(*self.application.sql.account_movements(acc_id, f, int(from_idx), int(to_idx)))
        r = {
            'items': list(cur.fetchall())
        }
        cur.execute(*self.application.sql.count_account_movements(acc_id, f))
        r['count'] = cur.fetchone()[0]
        return r


class AccountAmountHandler (JsonBaseHandler):
    def do(self, cur, acc_id):
        uid = self.current_user
        if (not self.application.has_or_had_account(cur, uid, acc_id) and
            not self.application.has_permission_by_account(cur, self.application.sql.P_canCheckAccounts, uid, acc_id) and
            not self.application.check_membership_by_kitty(cur, uid, acc_id)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.sql.account_amount(acc_id))
        v = cur.fetchone()
        return v[0] or 0.0, v[1]


class CsaInfoHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if not self.application.is_member_of_csa(cur, uid, csa_id, False):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.sql.csa_info(csa_id))
        r = self.application.sql.fetch_object(cur)
        cur.execute(*self.application.sql.csa_account(csa_id, self.application.sql.At_Kitty, full=True))
        r['kitty'] = self.application.sql.fetch_object(cur)  # FIXME: più di uno!
        cur.execute(*self.application.sql.csa_last_kitty_deposit(r['kitty']['id']))
        r['last_kitty_deposit'] = self.application.sql.fetch_object(cur)
        return r


class CsaUpdateHandler (JsonBaseHandler):
    def do(self, cur):
        uid = self.current_user
        csa = self.payload
        if not self.application.has_permission_by_csa(cur, self.application.sql.P_csaEditor, uid, csa['id']):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.sql.csa_update(csa))


class CsaListHandler (JsonBaseHandler):
    def do(self, cur):
        uid = self.current_user
        cur.execute(*self.application.sql.csa_list(uid))
        return self.application.sql.iter_objects(cur)


class CsaChargeMembershipFeeHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, self.application.sql.P_canEditMembershipFee, uid, csa_id):
            raise GDataException(error_codes.E_permission_denied, 403)

        p = self.payload
        t_desc = p['description']
        amount = p['amount']
        kitty_id = p['kitty']
        if amount < 0:
            raise GDataException(error_codes.E_illegal_amount)
        now = datetime.datetime.utcnow()
        cur.execute(*self.application.sql.csa_account(csa_id, self.application.sql.At_Kitty, accId=kitty_id, full=True))
        acc = self.application.sql.fetch_object(cur)
        if acc is None:
            raise GDataException(error_codes.E_illegal_kitty)
        currencyId = acc['currency_id']
        cur.execute(*self.application.sql.insert_transaction(t_desc,
                                            now,
                                            self.application.sql.Tt_MembershipFee,
                                            currencyId,
                                            csa_id
                                            )
                    )
        tid = cur.lastrowid
        cur.execute(*self.application.sql.insert_transaction_line_membership_fee(tid, amount, csa_id, currencyId))

        cur.execute(*self.application.sql.insert_transaction_line(tid, '', +1, kitty_id))
        last_line_id = cur.lastrowid
        cur.execute(*self.application.sql.transaction_calc_last_line_amount(tid, last_line_id))
        a = cur.fetchone()[0]
        # involvedAccounts[lastAccId] = str(a)
        cur.execute(*self.application.sql.transaction_fix_amount(last_line_id, a))

        cur.execute(*self.application.sql.log_transaction(tid, uid, self.application.sql.Tl_Added, self.application.sql.Tn_kitty_deposit, now))
        return { 'tid': tid }


class CsaRequestMembershipHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if self.application.is_member_of_csa(cur, uid, csa_id, True):
            raise GDataException(error_codes.E_already_member)
        profiles, contacts, args = self.application.sql.people_profiles1([uid])
        cur.execute(profiles, args)
        profile = self.application.sql.fetch_object(cur)
        cur.execute(contacts, args)
        contacts = list(self.application.sql.iter_objects(cur))

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
        cur.execute(*self.application.sql.csa_delivery_places(csa_id))
        return self.application.sql.iter_objects(cur)


class CsaDeliveryDatesHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        if not self.application.is_member_of_csa(cur, uid, csa_id, True):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.sql.csa_delivery_dates(csa_id, p['from'], p['to']))
        r = self.application.sql.iter_objects(cur)
        if len(r):
            # cur.execute(*self.application.sql.csa_delivery_shifts(set([ s['id'] for s in r ])))
            # for s in self.application.sql.iter_objects(cur):
            #    d = s['delivery_date_id']
            #
            for s in r:
                cur.execute(*self.application.sql.csa_delivery_shifts(s['id']))
                s['shifts'] = self.application.sql.iter_objects(cur)
        return r


class CsaAddShiftHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        if not self.application.is_member_of_csa(cur, uid, csa_id, True):
            raise GDataException(error_codes.E_permission_denied, 403)

        if uid != p['person_id'] and \
           not self.application.has_permission_by_csa(cur, self.application.sql.P_canManageShifts, uid, csa_id):
            raise GDataException(error_codes.E_permission_denied, 403)

        delivery_date_id = p['delivery_date_id']
        shift_id = p['id']
        if shift_id is None:
            cur.execute(*self.application.sql.csa_delivery_date_check(csa_id, delivery_date_id))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
            cur.execute(*self.application.sql.csa_delivery_shift_add(p))
            return {'id': cur.lastrowid}
        else:
            cur.execute(*self.application.sql.csa_delivery_shift_check(csa_id, shift_id))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
            cur.execute(*self.application.sql.csa_delivery_shift_update(shift_id, p['role']))


class CsaRemoveShiftHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload

        shift_id = p['id']
        if self.application.has_permission_by_csa(cur, self.application.sql.P_canManageShifts, uid, csa_id):
            cur.execute(*self.application.sql.csa_delivery_shift_check(csa_id, shift_id))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
        else:
            cur.execute(*self.application.sql.csa_delivery_shift_check(csa_id, shift_id, uid))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)

        cur.execute(*self.application.sql.csa_delivery_shift_remove(shift_id))


class AccountXlsHandler (BaseHandler):
    def get(self, acc_id):
        uid = self.current_user
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/vnd.ms-excel')
        self.clear_header('Content-Disposition')
        self.add_header('Content-Disposition', 'attachment; filename="account-%s.xls"' % acc_id)
        with self.application.conn as cur:
            if (not self.application.has_or_had_account(cur, uid, acc_id) and
                not self.application.has_permission_by_account(cur, self.application.sql.P_canCheckAccounts, uid, acc_id) and
                not self.application.check_membership_by_kitty(cur, uid, acc_id)
                ):
                raise HTTPError(403)
            style = xlwt.XFStyle()
            style.num_format_str='YYYY-MM-DD' # FIXME: i18n
            w = xlwt.Workbook(encoding='utf-8')
            s = w.add_sheet('Conto') # FIXME: correggere e i18n
            cur.execute(*self.application.sql.account_movements(acc_id, None, None, None))
            # t.description, t.transaction_date, l.description, l.amount, t.id, c.symbol, t.cc_type
            row = 1
            tdescmaxlength = 0
            ldescmaxlength = 0
            s.write(0, 0, "Data") # FIXME: i18n
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
        if not self.application.has_permission_by_account(cur, self.application.sql.P_canCloseAccounts, uid, acc_id):
            raise GDataException(error_codes.E_permission_denied, 403)
        # marca chiuso
        now = datetime.datetime.utcnow()
        owner_id = p['owner']
        tdesc = p.get('tdesc', '')
        cur.execute(*self.application.sql.account_close(now, acc_id, owner_id))
        affected_rows = cur.rowcount
        if affected_rows == 0:
            log_gassman.warning('not owner, can\'t close account: account=%s, owner=%s', acc_id, owner_id)
            return { 'error': error_codes.E_not_owner_or_already_closed }
        if affected_rows > 1:
            log_gassman.error('multiple account assignments: account=%s, owner=%s, rows=%s', acc_id, owner_id, affected_rows)
        # calcola saldo
        cur.execute(*self.application.sql.account_has_open_owners(acc_id))
        if cur.fetchone() is not None:
            log_gassman.info('account still in use, no need for a "z" transaction: account=%s', acc_id)
            return {
                'info': error_codes.I_account_open
            }
        else:
            cur.execute(*self.application.sql.account_amount(acc_id, returnCurrencyId=True))
            v = cur.fetchone()
            amount = v[0] or 0.0
            currencyId = v[2]
            if amount == 0.0:
                log_gassman.info('closed account was empty, no "z" transaction needed: account=%s')
                return {
                    'info': error_codes.I_empty_account
                }
            if amount != 0.0:
                # crea transazione z
                cur.execute(*self.application.sql.csa_by_account(acc_id))
                csa_id = cur.fetchone()[0]
                cur.execute(*self.application.sql.csa_account(csa_id, self.application.sql.At_Kitty, currencyId))
                kitty_id = cur.fetchone()[0]

                cur.execute(*self.application.sql.insert_transaction(
                    tdesc,
                    now,
                    self.application.sql.Tt_AccountClosing,
                    currencyId,
                    csa_id
                ))
                tid = cur.lastrowid
                cur.execute(*self.application.sql.insert_transaction_line(tid, '', amount, kitty_id))
                cur.execute(*self.application.sql.insert_transaction_line(tid, '', -amount, acc_id))
                last_line_id = cur.lastrowid
                cur.execute(*self.application.sql.transaction_calc_last_line_amount(tid, last_line_id))
                a = cur.fetchone()[0]
                #involvedAccounts[lastacc_id] = str(a)
                cur.execute(*self.application.sql.transaction_fix_amount(last_line_id, a))

                cur.execute(*self.application.sql.log_transaction(tid, uid, self.application.sql.Tl_Added, self.application.sql.Tn_account_closing, now))
                return {
                    'tid': tid
                }


# lo lascio per futura pagina diagnostica: deve comunque ritornare sempre 0.0
# class CsaAmountHandler (JsonBaseHandler):
#    def do(self, cur, csa_id):
#        uid = self.current_user
#        if not self.application.has_permission_by_csa(cur, sql.P_canCheckAccounts, uid, csa_id):
#            raise GDataException(error_codes.E_permission_denied)
#        cur.execute(*self.application.sql.csa_amount(csa_id))
#        return cur.fetchone()


# TODO: riprisitnare quando si edita il profilo utente
# class PermissionsHandler (JsonBaseHandler):
#    '''Restituisce tutti i permessi visibili dall'utente loggato.
#    '''
#    def do(self, cur):
#        u = self.application.session(self).get_logged_user('not authenticated')
#        cur.execute(*self.application.sql.find_visible_permissions(u.id))
#        return list(cur)


# class ProfileInfoHandler (JsonBaseHandler):
#    def do(self, cur):
#        uid = self.current_user
#        if uid is None:
#            raise GDataException(error_codes.E_not_authenticated, 401)
#        cur.execute(*self.application.sql.find_user_permissions(uid))
#        pp = [ p[0] for p in cur ]
#        cur.execute(*self.application.sql.find_user_csa(uid))
#        csa = { id: { 'name': name, 'member': member } for id, name, member in cur.fetchall() }
#        cur.execute(*self.application.sql.find_user_accounts(uid))
#        accs = list(cur)
#        pq, cq, a = self.application.sql.people_profiles1([uid])
#        cur.execute(pq, a)
#        profile = self.application.sql.fetch_object(cur)
#        cur.execute(cq, a)
#        contacts = self.application.sql.iter_objects(cur)
#        for c in contacts:
#            c.pop('person_id')
#            c.pop('priority')
#        return dict(
#            profile = profile,
#            permissions = pp,
#            csa = csa,
#            accounts = accs,
#            contacts=contacts
#        )


class AccountsIndexHandler (JsonBaseHandler):
    def do(self, cur, csa_id, from_idx, to_idx):
        p = self.payload
        q = p.get('q')
        if q:
            q = '%%%s%%' % q
        dp = p['dp']
        ex = p.get('ex', False)
        o = self.application.sql.accounts_index_order_by[int(p['o'])]
        uid = self.current_user
        can_check_accounts = self.application.has_permission_by_csa(cur, self.application.sql.P_canCheckAccounts, uid, csa_id)
        can_view_contacts = self.application.has_permission_by_csa(cur, self.application.sql.P_canViewContacts, uid, csa_id)
        viewable_contacts = p.get('vck', self.application.viewable_contact_kinds) if can_view_contacts else None
        if can_check_accounts:
            cur.execute(*self.application.sql.accounts_index(csa_id, q, dp, o, ex, int(from_idx), int(to_idx), search_contact_kinds=viewable_contacts))
        elif can_view_contacts:
            cur.execute(*self.application.sql.people_index(csa_id, q, dp, o, ex, int(from_idx), int(to_idx), search_contact_kinds=viewable_contacts))
        else:
            raise GDataException(error_codes.E_permission_denied, 403)
        r = {
            'items': list(cur)
        }
        if len(r['items']):
            cur.execute(*self.application.sql.count_people(csa_id, q, dp, ex, search_contact_kinds=viewable_contacts))
            r['count'] = cur.fetchone()[0]
        else:
            r['count'] = 0
        return r


class AccountsNamesHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        if not self.application.has_permissions(cur, self.application.sql.editableTransactionPermissions, uid, csa_id):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.sql.account_currencies(csa_id))
        account_curs = list(cur)
        cur.execute(*self.application.sql.account_people(csa_id))
        account_people = list(cur)
        cur.execute(*self.application.sql.account_people_addresses(csa_id))
        account_people_addresses = list(cur)
        cur.execute(*self.application.sql.csa_account(csa_id, self.application.sql.At_Kitty, full=True))
        kitty = {
            x['id']: x for x in self.application.sql.iter_objects(cur)
            }
        return dict(
            accountCurrencies=account_curs,
            accountPeople=account_people,
            accountPeopleAddresses=account_people_addresses,
            kitty=kitty,
            )


class TransactionEditHandler (JsonBaseHandler):
    def do(self, cur, csa_id, trans_id):
        uid = self.current_user
        cur.execute(*self.application.sql.transaction_edit(trans_id))

        r = self.application.sql.fetch_struct(cur)
        r['transId'] = trans_id

        ccType = r['cc_type']
        # regole per editare:
        # è D, ho P_canEnterDeposit e l'ho creata io
        # è P, ho P_canEnterPayments e l'ho creata io
        # oppure P_canManageTransactions
        if (not self.application.has_permissions(
                cur,
                [self.application.sql.P_canManageTransactions, self.application.sql.P_canCheckAccounts],
                uid, csa_id) and
            not self.application.is_kitty_transition_and_is_member(cur, trans_id, uid) and
            not (ccType in self.application.sql.editableTransactions and
                 self.application.has_permission_by_csa(
                     cur,
                     self.application.sql.transactionPermissions.get(ccType),
                     uid, csa_id) and
                 self.application.is_transaction_editor(cur, trans_id, uid)
                 ) and
            not self.application.isInvolvedInTransaction(cur, trans_id, uid)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)

        p = self.payload
        cur.execute(*self.application.sql.transaction_lines(trans_id))
        r['lines'] = [dict(account=l[1], notes=l[2], amount=l[3]) for l in cur]

        accountPeopleIndex = {}
        r['people'] = accountPeopleIndex
        cur.execute(*self.application.sql.transaction_people(trans_id))
        for acc_id, person_id in cur.fetchall():
            pp = accountPeopleIndex.setdefault(acc_id, [])
            pp.append(person_id)
        if p.get('fetchKitty'):
            cur.execute(*self.application.sql.csa_account(csa_id, self.application.sql.At_Kitty, full=True))
            r['kitty'] = {
                x['id']: x for x in self.application.sql.iter_objects(cur)
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
        tlogtype = None
        tlogdesc = error_codes.E_ok
        if tdesc is None:
            tdesc = datetime.datetime.utcnow()
        if trans_id is None:
            oldCc = None
            oldDesc = None
        else:
            trans_id = int(trans_id)
            cur.execute(*self.application.sql.transaction_type(trans_id))
            oldCc, oldDesc, modifiedBy = cur.fetchone()
            if modifiedBy is not None:
                raise GDataException(error_codes.E_already_modified)

        if ttype in (
                self.application.sql.Tt_Deposit,
                self.application.sql.Tt_CashExchange,
                self.application.sql.Tt_Withdrawal,
                self.application.sql.Tt_MembershipFee,
                self.application.sql.Tt_Payment
        ):
            if oldCc is not None and oldCc != ttype:
                raise GDataException(error_codes.E_type_mismatch)
            if len(tlines) == 0:
                raise GDataException(error_codes.E_no_lines)
            if ((not self.application.has_permission_by_csa(cur, self.application.sql.transactionPermissions[ttype], uid, csa_id) or
                (trans_id is not None and not self.application.is_transaction_editor(cur, trans_id, uid))) and
                not self.application.has_permission_by_csa(cur, self.application.sql.P_canManageTransactions, uid, csa_id)):
                raise GDataException(error_codes.E_permission_denied)

            cur.execute(*self.application.sql.insert_transaction(tdesc, tdate, self.application.sql.Tt_Unfinished, tcurr, csa_id))
            tid = cur.lastrowid
            if tid == 0:
                raise GDataException(error_codes.E_illegal_currency)

            customCsaAccounts = dict(
                EXPENSE=None,
                INCOME=None,
                KITTY=None
            )
            for l in tlines:
                desc = l['notes']
                amount = l['amount']
                reqAccId = l['account']
                if reqAccId in customCsaAccounts:
                    acc_id = customCsaAccounts[reqAccId]
                    if acc_id is None:
                        cur.execute(*self.application.sql.csa_account(csa_id, reqAccId, tcurr))
                        acc_id = cur.fetchone()[0]
                        customCsaAccounts[reqAccId] = acc_id
                else:
                    acc_id = reqAccId
                cur.execute(*self.application.sql.insert_transaction_line(tid, desc, amount, acc_id))
                last_line_id = cur.lastrowid

            cur.execute(*self.application.sql.check_transaction_coherency(tid))
            v = list(cur)
            if len(v) != 1:
                ttype = self.application.sql.Tt_Error
                tlogtype = self.application.sql.Tl_Error
                tlogdesc = error_codes.E_accounts_not_omogeneous_for_currency_and_or_csa
            elif v[0][1] != csa_id:
                ttype = self.application.sql.Tt_Error
                tlogtype = self.application.sql.Tl_Error
                tlogdesc = error_codes.E_accounts_do_not_belong_to_csa
            else:
                cur.execute(*self.application.sql.transaction_calc_last_line_amount(tid, last_line_id))
                a = cur.fetchone()[0]
                # involvedAccounts[lastAccId] = str(a)
                cur.execute(*self.application.sql.transaction_fix_amount(last_line_id, a))
                tlogtype = self.application.sql.Tl_Added if trans_id is None else self.application.sql.Tl_Modified

        elif ttype == self.application.sql.Tt_Trashed:
            if oldCc not in self.application.sql.deletableTransactions:
                raise GDataException(error_codes.E_illegal_delete)
            if len(tlines) > 0:
                raise GDataException(error_codes.E_trashed_transactions_can_not_have_lines)
            if trans_id is None:
                raise GDataException(error_codes.E_missing_trashId_of_transaction_to_be_deleted)
            if ((not self.application.has_permissions(cur, self.application.sql.editableTransactionPermissions, uid, csa_id) or
                not self.application.is_transaction_editor(cur, trans_id, uid)) and
                not self.application.has_permission_by_csa(cur, self.application.sql.P_canManageTransactions, uid, csa_id)):
                raise GDataException(error_codes.E_permission_denied)
            cur.execute(*self.application.sql.insert_transaction(tdesc, tdate, self.application.sql.Tt_Unfinished, tcurr, csa_id))
            tid = cur.lastrowid
            if tid == 0:
                raise GDataException(error_codes.E_illegal_currency)
            tlogtype = self.application.sql.Tl_Deleted
            # tlogdesc = ''

        else:
            log_gassman.error('illegal transaction type: %s', tdef)
            raise GDataException(error_codes.E_illegal_transaction_type)

        cur.execute(*self.application.sql.finalize_transaction(tid, ttype))
        cur.execute(*self.application.sql.log_transaction(tid, uid, tlogtype, tlogdesc, datetime.datetime.utcnow()))
        if trans_id is not None and ttype != self.application.sql.Tt_Error:
            cur.execute(*self.application.sql.update_transaction(trans_id, tid))
        if ttype == self.application.sql.Tt_Error:
            raise GDataException(tlogdesc)
        else:
            self.notify_account_change(cur, tid, tdesc, tdate, trans_id, oldDesc)
        return tid

    # Transaction notification types
    Tnt_new_transaction = 'n'
    Tnt_amount_changed = 'a'
    Tnt_notes_changed = 'd'
    Tnt_transaction_removed = 'r'
    Tnt_description_changed = 'm'

    def notify_account_change(self, cur, trans_id, tdesc, tdate, modified_trans_id, oldDesc):
        cur.execute(*self.application.sql.transaction_fetch_lines_to_compare(modified_trans_id, trans_id))
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
        if modified_trans_id is not None and tdesc != oldDesc:
            for acc_id in newLines:
                if acc_id not in diffs:
                    diffs[acc_id] = [self.Tnt_description_changed, tdesc, oldDesc]
        if len(diffs) == 0:
            log_gassman.debug('nothing to notify for transaction %s modifying transaction %s', trans_id, modified_trans_id)
            return
        # FIXME: soglia specifica di csa
        LVL_THRES = -40
        #signalledPeople = dict() # da persone (pid) a lista di account ([accountId])
        accounts = dict() # da account (accountId) a lista di persone ([{first/middle/last_name, email}])
        # considero solo gli account i cui owner hanno nei settaggi la ricezione di ogni notifica
        cur.execute(*self.application.sql.account_owners_with_optional_email_for_notifications(diffs.keys()))
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
        cur.execute(*self.application.sql.account_total_for_notifications(accounts.keys()))
        for acc_id, total, curr_sym in cur.fetchall():
            accounts[acc_id]['account'] = (total, curr_sym)
        for acc_id, accData in accounts.items():
            total, curr_sym = accData['account']
            people = accData['people']
            notificationType = diffs[acc_id]
            receivers = [p['email'] for p in people if p['email']]
            if len(receivers) == 0:
                log_gassman.debug('transaction not notified, people do not have email account: people=%s, tid=%s', people, trans_id)
                continue
            cur.execute(*self.application.sql.person_notification_email(self.current_user))
            try:
                replyTo = cur.fetchone()[0]
            except:
                replyTo = None
            # TODO: Localizzazione del messaggio
            self.notify(
                'account_update',
                receivers=[p['email'] for p in people if p['email']],
                replyTo=replyTo,
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
                oldDesc=oldDesc,
                notificationType=notificationType,
                publishedUrl=settings.PUBLISHED_URL,
                Tnt_new_transaction=self.Tnt_new_transaction,
                Tnt_amount_changed=self.Tnt_amount_changed,
                Tnt_notes_changed=self.Tnt_notes_changed,
                Tnt_transaction_removed=self.Tnt_transaction_removed,
                Tnt_description_changed=self.Tnt_description_changed,
            )


class TransactionsEditableHandler (JsonBaseHandler):
    def do(self, cur, csa_id, from_idx, to_idx):
        q = '%%%s%%' % self.payload['q']
        o = self.application.sql.transactions_editable_order_by[int(self.payload['o'])]
        uid = self.current_user
        if self.application.has_permission_by_csa(cur, self.application.sql.P_canManageTransactions, uid, csa_id):
            cur.execute(*self.application.sql.transactions_all(csa_id, q, o, int(from_idx), int(to_idx)))
            q, a = self.application.sql.transactions_count_all(csa_id, q)
        elif self.application.has_permissions(cur, self.application.sql.editableTransactionPermissions, uid, csa_id):
            cur.execute(*self.application.sql.transactions_by_editor(csa_id, uid, q, o, int(from_idx), int(to_idx)))
            q, a = self.application.sql.transactions_count_by_editor(csa_id, uid, q)
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


def shortDate(d):
    return d.strftime('%Y/%m/%d') # FIXME il formato dipende dal locale dell'utente


def pubDate(d):
    return d.strftime('%a, %d %b %Y %H:%M:%S GMT')


def currency(v, sym):
    return '%s%s' % (v, sym)


class RssFeedHandler (tornado.web.RequestHandler):
    def get(self, rssId):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'text/xml')
        with self.application.conn as cur:
            cur.execute(*self.application.sql.rss_user(rssId))
            p = cur.fetchone()
            cur.execute(*self.application.sql.rss_feed(rssId))
            self.render('rss.xml',
                        person=p,
                        items=cur,
                        shortDate=shortDate,
                        pubDate=pubDate,
                        currency=currency,
                        )


class PeopleProfilesHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        pids = self.payload['pids']
        uid = self.current_user
        isSelf = len(pids) == 1 and (pids[0] == 'me' or int(pids[0]) == uid)
        if isSelf:
            if uid is None:
                raise GDataException(error_codes.E_not_authenticated, 401)
            pids = [uid]
        # if csa_id == 'null':
        #    if not isSelf:
        #        raise GDataException(error_codes.E_permission_denied, 403)
        #    csa_id = None
        if not isSelf and not self.application.is_member_of_csa(cur, uid, csa_id, False):
            raise GDataException(error_codes.E_permission_denied, 403)
        can_view_contacts = isSelf or self.application.has_permission_by_csa(cur, self.application.sql.P_canViewContacts, uid, csa_id)
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
            #p['profile'] = self.application.find_person_by_id(uid)
        else:
            accs, perms, args = self.application.sql.people_profiles2(csa_id, pids)
            canViewAccounts = isSelf or self.application.has_permission_by_csa(cur, self.application.sql.P_canCheckAccounts, uid, csa_id)
            cur.execute(accs, args)
            for acc in self.application.sql.iter_objects(cur):
                p = record(acc['person_id'])
                if canViewAccounts:
                    p['accounts'].append(acc)
            cur.execute(perms, args)
            for perm in self.application.sql.iter_objects(cur):
                p = record(perm['person_id'])
                if can_view_contacts:
                    p['permissions'].append(perm['perm_id'])
        if r.keys():
            profiles, contacts, args = self.application.sql.people_profiles1(r.keys())
            cur.execute(profiles, args)
            for prof in self.application.sql.iter_objects(cur):
                p = record(prof['id'])
                p['profile'] = prof
            if can_view_contacts:
                cur.execute(contacts, args)
                for addr in self.application.sql.iter_objects(cur):
                    p = record(addr['person_id'])
                    p['contacts'].append(addr)
            # TODO: indirizzi
        if isSelf:
            cur.execute(*self.application.sql.find_user_csa(uid))
            p = record(uid)
            p['csa'] = {
                id: {
                    'name': name,
                    'member': member
                } for id, name, member in cur.fetchall()
                }
        return r


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
            not self.application.has_permission_by_csa(cur, self.application.sql.P_canEditContacts, uid, csa_id) and
            uid != pid
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        # salva profilo
        cur.execute(*self.application.sql.updateProfile(profile))
        # salva contatti
        contacts = p['contacts']
        cur.execute(*self.application.sql.fetchContacts(pid))
        ocontacts = [x[0] for x in cur.fetchall()]
        if ocontacts:
            cur.execute(*self.application.sql.removeContactAddresses(ocontacts))
            cur.execute(*self.application.sql.removePersonContacts(ocontacts))
        for c, i in zip(contacts, range(len(contacts))):
            naddress = c['address']
            nkind = c['kind']
            ncontact_type = c['contact_type']
            if not naddress:
                continue
            if nkind == self.application.sql.Ck_Id:
                continue
            if nkind not in self.application.sql.Ckk:
                continue
            #naid = c['id']
            #npriority = ncontact['priority']
            cur.execute(*self.application.sql.saveAddress(naddress, nkind, ncontact_type))
            aid = cur.lastrowid
            cur.execute(*self.application.sql.linkAddress(pid, aid, i))
        # salva permessi
        permissions = p.get('permissions')
        if permissions is not None and \
           csa_id is not None and \
           self.application.has_permission_by_csa(cur, self.application.sql.P_canGrantPermissions, uid, csa_id):
            cur.execute(*self.application.sql.find_user_permissions(uid, csa_id))
            assignable_perms = set([row[0] for row in cur.fetchall()])
            cur.execute(*self.application.sql.revokePermissions(pid, csa_id, assignable_perms))
            for p in set(permissions) & assignable_perms:
                cur.execute(*self.application.sql.grantPermission(pid, p, csa_id))
        # TODO: salva indirizzi
        fee = p.get('membership_fee')
        if csa_id is not None and fee and self.application.has_permission_by_csa(cur, self.application.sql.P_canEditMembershipFee, uid, csa_id):
            # accId = fee.get('account')
            amount = fee.get('amount')
            if float(amount) >= 0:
                cur.execute(*self.application.sql.account_updateMembershipFee(csa_id, pid, amount))


class PersonCheckEmailHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        log_gassman.debug('saving: %s', p)
        pid = p['id']
        email = p['email']
        if (
            not self.application.has_permission_by_csa(cur, self.application.sql.P_canEditContacts, uid, csa_id) and
            uid != int(pid)
            ):
            raise GDataException(error_codes.E_permission_denied, 403)
        # verifica unicità
        cur.execute(*self.application.sql.isUniqueEmail(pid, email))
        return cur.fetchone()[0]


class EventSaveHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        log_gassman.debug('saving: %s', p)
        event_id = p.get('id')
        shifts = p.pop('shifts')

        if not self.application.has_permission_by_csa(cur, self.application.sql.P_canManageShifts, uid, csa_id):
            raise GDataException(error_codes.E_permission_denied, 403)

        if event_id is not None:
            cur.execute(*self.application.sql.csa_delivery_date_check(csa_id, event_id))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
            cur.execute(*self.application.sql.csa_delivery_date_update(**p))
            cur.execute(*self.application.sql.csa_delivery_shift_remove_all(event_id))
        else:
            cur.execute(*self.application.sql.csa_delivery_place_check(csa_id, p['delivery_place_id']))
            v = cur.fetchone()[0]
            if v == 0:
                raise GDataException(error_codes.E_permission_denied, 403)
            cur.execute(*self.application.sql.csa_delivery_date_save(**p))
            event_id = cur.lastrowid
        for shift in shifts:
            shift['delivery_date_id'] = event_id
            cur.execute(*self.application.sql.csa_delivery_shift_add(shift))
        return {
            'id': event_id
        }


class EventRemoveHandler (JsonBaseHandler):
    def do(self, cur, csa_id):
        uid = self.current_user
        p = self.payload
        log_gassman.debug('removing: %s', p)

        if not self.application.has_permission_by_csa(cur, self.application.sql.P_canManageShifts, uid, csa_id):
            raise GDataException(error_codes.E_permission_denied, 403)

        date_id = p['id']
        cur.execute(*self.application.sql.csa_delivery_date_check(csa_id, date_id))
        v = cur.fetchone()[0]
        if v == 0:
            raise GDataException(error_codes.E_permission_denied, 403)

        cur.execute(*self.application.sql.csa_delivery_shift_remove_all(date_id))
        cur.execute(*self.application.sql.csa_delivery_date_remove(date_id))


class AdminPeopleIndexHandler (JsonBaseHandler):
    def do(self, cur, from_idx, to_idx):
        p = self.payload

        q = p.get('q')
        if q:
            q = '%%%s%%' % q
        o = self.application.sql.admin_people_index_order_by[int(self.payload.get('o', 0))]
        uid = self.current_user
        if self.application.has_permission_by_csa(cur, sql.P_canAdminPeople, uid, None):
            csa = p.get('csa')
            vck = p.get('vck', self.application.viewable_contact_kinds)
            cur.execute(*self.application.sql.admin_people_index(
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
            cur.execute(*self.application.sql.admin_count_people(q, csa, vck))
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
        if not self.application.has_permission_by_csa(cur, sql.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        r = {}
        if len(pids) == 0:
            return r
        profiles, contacts, args = self.application.sql.people_profiles1(pids)
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

        for acc in self.application.sql.iter_objects(cur):
            p = record(acc['person_id'])
            p['contacts'].append(acc)
        cur.execute(profiles, args)
        for prof in self.application.sql.iter_objects(cur):
            p = record(prof['id'])
            p['profile'] = prof
        for pid, p in r.items():
            cur.execute(*self.application.sql.find_user_csa(pid))
            p['csa'] = self.application.sql.iter_objects(cur)
        return r


class AdminPeopleRemoveHandler (JsonBaseHandler):
    def do(self, cur):
        pid = self.payload['pid']
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, sql.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        # TODO: verificare che non abbia né abbia avuto conti
        cur.execute(*self.application.sql.find_user_csa(pid))
        if len(cur.fetchall()) > 0:
            raise GDataException(error_codes.E_cannot_remove_person_with_accounts)
        cur.execute(*self.application.sql.deleteContactsOfPerson(pid))
        cur.execute(*self.application.sql.deleteContactsPerson(pid))
        cur.execute(*self.application.sql.deletePermissions(pid))
        cur.execute(*self.application.sql.deletePerson(pid))


class AdminPeopleJoinHandler (JsonBaseHandler):
    def do(self, cur):
        newpid = self.payload['newpid']
        oldpid = self.payload['oldpid']
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, sql.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.sql.reassignContacts(newpid, oldpid))
        cur.execute(*self.application.sql.reassignPermissions(newpid, oldpid))
        cur.execute(*self.application.sql.reassignAccounts(newpid, oldpid))
        cur.execute(*self.application.sql.deletePerson(oldpid))


class AdminPeopleAddHandler (JsonBaseHandler):
    def do(self, cur):
        pid = self.payload['pid']
        acc = self.payload['acc']
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, sql.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        cur.execute(*self.application.sql.grantAccount(pid, acc, datetime.datetime.utcnow()))


class AdminPeopleCreateAccountHandler (JsonBaseHandler):
    def do(self, cur):
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, sql.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        pid = self.payload['pid']
        csa = self.payload['csa']
        cur.execute(*self.application.sql.csa_currencies(csa))
        for row in cur.fetchall():
            curr = row[0]
            cur.execute(*self.application.sql.account_create(
                '%s' % pid,
                self.application.sql.At_Asset,
                csa,
                curr,
                0.0
            ))
            accId = cur.lastrowid
            cur.execute(*self.application.sql.grantAccount(pid, accId, datetime.datetime.utcnow()))


class AdminPeopleCreateHandler (JsonBaseHandler):
    def do(self, cur):
        uid = self.current_user
        if not self.application.has_permission_by_csa(cur, sql.P_canAdminPeople, uid, None):
            raise GDataException(error_codes.E_permission_denied, 403)
        first_name = self.payload['first_name']
        last_name = self.payload['last_name']
        csa = self.payload.get('csa')
        cur.execute(*self.application.sql.create_person(first_name, '', last_name))
        pid = cur.lastrowid
        rfi = rss_feed_id(pid)
        cur.execute(*self.application.sql.assign_rss_feed_id(pid, rfi))
        if csa is not None:
            cur.execute(*self.application.sql.csa_currencies(csa))
            acc = []
            for row in cur.fetchall():
                curr = row[0]
                cur.execute(*self.application.sql.account_create(
                    '%s %s' % (first_name, last_name),
                    self.application.sql.At_Asset,
                    csa,
                    curr,
                    0.0
                ))
                accId = cur.lastrowid
                cur.execute(*self.application.sql.grantAccount(pid, accId, datetime.datetime.utcnow()))
                acc.append(accId)
        else:
            acc = None
        return { 'pid': pid, 'acc': acc }


def main():
    import ioc

    io_loop = ioc.io_loop()

    tornado.locale.load_translations(settings.TRANSLATIONS_PATH)

    mailer = ioc.mailer()

    application = GassmanWebApp(
        ioc.sql_factory(),
        mailer,
        ioc.db_connection_arguments(),
    )

    application.listen(settings.HTTP_PORT)

    log_gassman.info('GASsMAN web server up and running...')

    io_loop.start()

if __name__ == '__main__':
    main()
