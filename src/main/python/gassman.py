#!/usr/bin/env python3

'''
Created on 01/mar/2014

@author: makeroo
'''

import datetime
import hashlib
import logging.config
import os.path
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
import asyncsmtp

import gassman_version
import sql
import error_codes

log_gassman = logging.getLogger('gassman.application')

# TODO: db asincrono

def rss_feed_id (pid):
    return hashlib.sha256((settings.COOKIE_SECRET + str(pid)).encode('utf-8')).hexdigest()

class GoogleUser (object):
    authenticator = 'Google2'

    def __init__ (self, id_token):
        oauth2token = oauth2lib.extract_payload_from_oauth2_id_token(id_token['id_token'])
        self.userId = oauth2token['sub']
        self.email = oauth2token['email']
        self.access_token = id_token['access_token']

    @tornado.gen.coroutine
    def loadFullProfile (self):
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

#    def __getattr__ (self, name):
#        if 'name' in ['firstName', 'middleName', 'lastName', 'gProfile', 'picture']:
#            pass

class Session (object):
    def __init__ (self, app):
        self.application = app
        self.logged_user = None
        self.created = datetime.datetime.utcnow()
        self.registrationNotificationSent = False

#    def get_logged_user (self, error='not authenticated'):
#        if not self.logged_user:
#            if error:
#                raise Exception(error)
#            else:
#                return None
##        if self.logged_user.account is None:
##            # controllo per vedere se è avvenuta la registrazione
##            with self.application.conn as cur:
##                cur.execute(*self.application.sql.find_current_account(self.logged_user.id))
##                try:
##                    self.logged_user.account = int(cur.fetchone()[0])
##                except:
##                    etype, evalue, _ = sys.exc_info()
##                    log_gassman.debug('account not found: user=%s, cause=%s/%s', self.logged_user.id, etype, evalue)
#        return self.logged_user

class Person (object):
    class DoesNotExist (Exception):
        pass

    def __init__ (self, p_id, p_first_name, p_middle_name, p_last_name, p_rss_feed_id):
        self.id = p_id
        self.firstName = p_first_name
        self.middleName = p_middle_name
        self.lastName = p_last_name
        #self.account = p_current_account_id
        self.rssFeedId = p_rss_feed_id

    def __str__ (self):
        return '%s (%s %s)' % (self.id, self.firstName, self.lastName)

class GassmanWebApp (tornado.web.Application):
    def __init__ (self, sql, mailer, connArgs):
        handlers = [
            (r'^/$', IndexHandler),
            (r'^/login.html$', LoginHandler),
            (r'^/home.html$', HomeHandler),
            (r'^/auth/google$', GoogleAuthLoginHandler),
            (r'^/sys/version$', SysVersionHandler),
            (r'^/account/(\d+)/owner$', AccountOwnerHandler),
            (r'^/account/(\d+)/movements/(\d+)/(\d+)$', AccountMovementsHandler),
            (r'^/account/(\d+)/amount$', AccountAmountHandler),
            (r'^/account/(\d+)/xls$', AccountXlsHandler),
            (r'^/profile-info$', ProfileInfoHandler),
            (r'^/accounts/(\d+)/index/(\d+)/(\d+)$', AccountsIndexHandler),
            (r'^/accounts/(\d+)/names$', AccountsNamesHandler),
            (r'^/expenses/(\d+)/tags$', ExpensesNamesHandler),
            (r'^/transaction/(\d+)/(\d+)/edit$', TransactionEditHandler),
            (r'^/transaction/(\d+)/save$', TransactionSaveHandler),
            (r'^/transactions/(\d+)/editable/(\d+)/(\d+)$', TransactionsEditableHandler),
            (r'^/csa/(\d+)/info$', CsaInfoHandler),
            (r'^/csa/list', CsaListHandler),
            (r'^/csa/(\d+)/charge_membership_fee$', CsaChargeMembershipFeeHandler),
            (r'^/csa/(\d+)/request_membership$', CsaRequestMembershipHandler),
            (r'^/csa/(\d+)/delivery_places$', CsaDeliveryPlacesHandler),
            #(r'^/csa/(\d+)/total_amount$', CsaAmountHandler),
            (r'^/rss/(.+)$', RssFeedHandler),
            (r'^/people/(null|\d+)/profiles$', PeopleProfilesHandler),
            (r'^/person/(null|\d+)/save$', PersonSaveHandler),
            (r'^/person/(\d+)/check_email$', PersonCheckEmailHandler),
            ]
        #codeHome = os.path.dirname(__file__)
        sett = dict(
            cookie_secret = settings.COOKIE_SECRET,
            template_path = settings.TEMPLATE_PATH, #os.path.join(codeHome, 'templates'),
            static_path = settings.STATIC_PATH, #os.path.join(codeHome, "static"),
            xsrf_cookies = True,
            xsrf_cookie_version = 1,
            login_url = '/login.html',
            google_oauth = {
                            "key": settings.GOOGLE_OAUTH2_CLIENTID,
                            "secret": settings.GOOGLE_OAUTH2_SECRET,
                            },
            google_oauth_redirect=settings.GOOGLE_OAUTH2_REDIRECT,
            debug = settings.DEBUG_MODE,
            )
        super().__init__(handlers, **sett)
        self.mailer = mailer
        self.connArgs = connArgs
        self.conn = None
        self.sql = sql
        self.sessions = dict()
        self.connect()
        tornado.ioloop.PeriodicCallback(self.checkConn, settings.DB_CHECK_INTERVAL).start()

    def connect (self):
        if self.conn is not None:
            try:
                self.conn.close()
                self.conn = None
            except:
                pass
        self.conn = pymysql.connect(**self.connArgs)

    def checkConn (self):
        try:
            try:
                with self.conn as cur:
                    cur.execute(self.sql.checkConn())
                    list(cur)
            except pymysql.err.OperationalError as e:
                if e.args[0] == 2013: # pymysql.err.OperationalError: (2013, 'Lost connection to MySQL server during query')
                    # provo a riconnettermi
                    log_gassman.warning('mysql closed connection, reconnecting')
                    self.conn = self.connect()
                else:
                    raise
        except:
            etype, evalue, tb = sys.exc_info()
            log_gassman.fatal('db connection failed: cause=%s/%s', etype, evalue)
            self.notify('[FATAL] No db connection', 'Connection error: %s/%s.\nTraceback:\n%s' %
                           (etype, evalue, loglib.TracebackFormatter(tb))
                           )

    def notify (self, subject, body, receivers = None):
        if self.mailer is None:
            log_gassman.info('SMTP not configured, mail not sent: %s\n%s', subject, body)
        else:
            self.mailer.send(settings.SMTP_SENDER,
                             receivers or settings.SMTP_RECEIVER,
                             '[GASsMan] %s' % subject,
                             body
                             )

    def hasAccount (self, cur, pid, accId):
        cur.execute(*self.sql.has_account(pid, accId))
        return cur.fetchone()[0] > 0

    def add_contact (self, cur, pid, addr, kind, notes):
        if addr:
            cur.execute(*self.sql.create_contact(addr, kind, notes))
            cid = cur.lastrowid
            cur.execute(*self.sql.assign_contact(cid, pid))

    @tornado.gen.coroutine
    def checkProfile (self, requestHandler, user):
        with self.conn as cur:
            authMode = (user.userId, user.authenticator, sql.Ck_Id)
            cur.execute(*self.sql.check_user(*authMode))
            pp = list(cur)
            if len(pp) == 0:
                log_gassman.debug('profile not found: credentials=%s', authMode)
                authMode = (user.email, 'verified', sql.Ck_Email)
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
            attrsToComplete = [('email', self.sql.Ck_Email, 'verified'),
                               ('gProfile', self.sql.Ck_GProfile, ''),
                               ('picture', self.sql.Ck_Picture, ''),
                               ]
            contactToDelete = None
            if p is None:
                pass
            elif authMode[2] == sql.Ck_Email:
                cur.execute(*self.sql.fetchAllContacts(p.id))
                for pcId, aId, kind, contactType in list(cur):
                    if kind == self.sql.Ck_Id and contactType == 'Google':
                        contactToDelete = (pcId, aId)
                    else:
                        attrsToComplete = list(filter(lambda x: x[1] != kind, attrsToComplete))
                if contactToDelete is None:
                    attrsToComplete = []
            else:
                attrsToComplete = []
            if contactToDelete:
                cur.execute(*self.sql.removePersonContact(contactToDelete[0]))
                cur.execute(*self.sql.removeContactAddress(contactToDelete[1]))
            if attrsToComplete:
                try:
                    yield user.loadFullProfile()
                    # non ho trovato niente su db
                    cur.execute(*self.sql.create_contact(user.userId, self.sql.Ck_Id, user.authenticator))
                    contactId = cur.lastrowid
                    if p is None:
                        cur.execute(*self.sql.create_person(user.firstName, user.middleName, user.lastName))
                        p_id = cur.lastrowid
                        rfi = rss_feed_id(p_id)
                        cur.execute(*self.sql.assign_rss_feed_id(p_id, rfi))
                        p = Person(p_id, user.firstName, user.middleName, user.lastName, rfi)
                        log_gassman.info('profile created: newUser=%s', p)
                    else:
                        p_id = p.id
                    cur.execute(*self.sql.assign_contact(contactId, p_id))
                    for attrName, kind, notes in attrsToComplete:
                        self.add_contact(cur, p_id, getattr(user, attrName), kind, notes)
                    #self.add_contact(cur, p_id, user.email, self.sql.Ck_Email, '')
                    #self.add_contact(cur, p_id, user.gProfile, self.sql.Ck_GProfile, '')
                    #self.add_contact(cur, p_id, user.picture, self.sql.Ck_Picture, '')
                except:
                    etype, evalue, tb = sys.exc_info()
                    log_gassman.error('profile creation failed: cause=%s/%s\nfull stacktrace:\n%s', etype, evalue, loglib.TracebackFormatter(tb))
                    self.notify('[ERROR] User profile creation failed', 'Cause: %s/%s\nAuthId: %s (%s %s)\nTraceback:\n%s' %
                                   (etype, evalue, user.userId, user.firstName, user.lastName, loglib.TracebackFormatter(tb))
                                   )
        if p is not None:
            requestHandler.set_secure_cookie("user", tornado.escape.json_encode(p.id))
        return p

    def session (self, requestHandler):
        xt = requestHandler.xsrf_token
        s = self.sessions.get(xt, None)
        if s is None:
            s = Session(self)
            self.sessions[xt] = s
            pid = requestHandler.current_user
            if pid:
                with self.conn as cur:
                    cur.execute(*self.sql.find_person(pid))
                    pdata = cur.fetchone()
                    if pdata:
                        s.logged_user = Person(*pdata)
                        log_gassman.info('created session: user=%s, agent=%s, from=%s', s.logged_user, requestHandler.request.headers['User-Agent'], requestHandler.request.headers.get('X-Forwarded-For', 'NA'))
                    else:
                        log_gassman.warning('created session, user not found: pid=%s, agent=%s, from=%s', pid, requestHandler.request.headers['User-Agent'], requestHandler.request.headers.get('X-Forwarded-For', 'NA'))
            else:
                log_gassman.info('created session: agent=%s, from=%s', requestHandler.request.headers['User-Agent'], requestHandler.request.headers.get('X-Forwarded-For', 'NA'))
        return s

    def checkMembershipByKitty (self, cur, personId, accId):
        cur.execute(*self.sql.check_membership_by_kitty(personId, accId))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('check membership by kitty: user=%s, acc=%s, r=%s', personId, accId, r)
        return r

    def hasPermissionByAccount (self, cur, perm, personId, accId):
        cur.execute(*self.sql.has_permission_by_account(perm, personId, accId))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permission: user=%s, perm=%s, r=%s', personId, perm, r)
        return r

    def hasPermissionByCsa (self, cur, perm, personId, csaId):
        if perm is None:
            return False
        cur.execute(*self.sql.has_permission_by_csa(perm, personId, csaId))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permission: user=%s, perm=%s, r=%s', personId, perm, r)
        return r

    def hasPermissions (self, cur, perms, personId, csaId):
        cur.execute(*self.sql.has_permissions(perms, personId, csaId))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permissions: user=%s, perm=%s, r=%s', personId, perms, r)
        return r

    def isTransactionEditor (self, cur, transId, personId):
        '''
        Una transazione può essere creata/modificata da chi ha canEnterXX
        o da chi ha manageTrans.
        Per verificare devo risalire la catena delle sovrascritture.
        '''
        while transId is not None:
            cur.execute(*self.sql.log_transaction_check_operator(personId, transId))
            if cur.fetchone()[0] > 0:
                return True
            cur.execute(*self.sql.transaction_previuos(transId))
            l = cur.fetchone()
            transId = l[0] if l is not None else None
        return False

    def isInvolvedInTransaction (self, cur, transId, personId):
        while transId is not None:
            cur.execute(*self.sql.transaction_is_involved(transId, personId))
            if cur.fetchone()[0] > 0:
                return True
            cur.execute(*self.sql.transaction_previuos(transId))
            l = cur.fetchone()
            transId = l[0] if l is not None else None
        return False

class BaseHandler (tornado.web.RequestHandler):
    def get_current_user (self):
        c = self.get_secure_cookie('user', max_age_days=settings.COOKIE_MAX_AGE_DAYS)
        return int(c) if c else None

    def get_logged_user (self, session=None, error=error_codes.E_not_authenticated):
        uid = self.get_current_user()
        if uid is not None:
            if session is None:
                session = self.application.session(self)
            p = session.logged_user
            if p is not None and p.id == uid:
                return p
        if error:
            raise Exception(error)
        return None

    def notify (self, template, receivers = None, **namespace):
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
            receivers
        )

class IndexHandler (BaseHandler):
    def get (self):
        p = self.get_logged_user(None, None)
        log_gassman.debug('index: lu=%s', p)
        if p is None:
            self.redirect("/login.html")
        else: #if self.application.hasAccounts(p.id):
            self.redirect("/home.html")
#        else:
#            self.redirect("/incomplete_profile.html")

class LoginHandler (BaseHandler):
    def get (self):
        p = self.get_logged_user(None, None)
        if p is None:
            self.render('login.html',
                        LOCALE=self.locale.code,
                        )
        else: #if self.application.hasAccounts(p.id):
            self.redirect("/home.html")

class GoogleAuthLoginHandler (tornado.web.RequestHandler, tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            id_token = yield self.get_authenticated_user(
                redirect_uri=self.settings['google_oauth_redirect'],
                code=self.get_argument('code')
                )
            token_user = GoogleUser(id_token)
            _person = yield self.application.checkProfile(self, token_user)
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
    @tornado.web.authenticated
    def get (self):
        p = self.get_logged_user(None, None)
        if p is None:
            self.redirect('/login.html')
        else: #if self.application.hasAccounts(p.id):
            self.render('home.html',
                        LOCALE=self.locale.code,
                        )

class JsonBaseHandler (BaseHandler):
    notifyExceptions = False

    def post (self, *args):
        with self.application.conn as cur:
            m = cur.execute
            def logging_execute (sql, *args):
                if not sql.upper().startswith('SELECT'):
                    log_gassman.debug('SQL: %s / %s', sql, args)
                m(sql, *args)
            cur.execute = logging_execute
            r = self.do(cur, *args)
            self.write_response(r)

    def write_response (self, data):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        jsonlib.write_json(data, self)

    def write_error(self, status_code, **kwargs):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        etype, evalue, tb = kwargs.get('exc_info', ('', '', None))
        if self.notifyExceptions:
            self.application.notify('[ERROR] Json API Failed',
                                    'Request error:\ncause=%s/%s\nother args: %s\nTraceback:\n%s' %
                                    (etype, evalue, kwargs, loglib.TracebackFormatter(tb))
                                    )
        if hasattr(evalue, 'args'):
            i = [ str(etype) ] + [ str(x) for x in evalue.args ]
        else:
            i = [ str(etype), str(evalue) ]
        # tanto logga tornado
        #log_gassman.error('unexpected exception: %s/%s', etype, evalue)
        #log_gassman.debug('full stacktrace:\n', loglib.TracebackFormatter(tb))
        jsonlib.write_json(i, self)

    @property
    def payload (self):
        if not hasattr(self, '_payload'):
            try:
                x = self.request.body
                s = x.decode('utf8')
                self._payload = json.loads(s)
            except:
                etype, evalue, tb = sys.exc_info()
                log_gassman.error('illegal payload: cause=%s/%s', etype, evalue)
                log_gassman.debug('full stacktrace:\n%s', loglib.TracebackFormatter(tb))
                raise Exception(error_codes.E_illegal_payload)
        return self._payload

class SysVersionHandler (JsonBaseHandler):
    def post (self):
        data = [ gassman_version.version ]
        self.write_response(data)

class AccountOwnerHandler (JsonBaseHandler):
    def do (self, cur, accId):
        u = self.get_logged_user()
        if (not self.application.hasAccount(cur, u.id, accId) and
            not self.application.hasPermissionByAccount(cur, sql.P_canCheckAccounts, u.id, accId) and
            not self.application.checkMembershipByKitty(cur, u.id, accId)
            ):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.sql.account_owners(accId))
        oo = list(cur)
        if oo:
            return dict(people=oo)
        # se il conto non è di una persona, sarà del csa
        cur.execute(*self.application.sql.account_description(accId))
        return dict(desc=cur.fetchone())

class AccountMovementsHandler (JsonBaseHandler):
    def do (self, cur, accId, fromIdx, toIdx):
        u = self.get_logged_user()
        if (not self.application.hasAccount(cur, u.id, accId) and
            not self.application.hasPermissionByAccount(cur, sql.P_canCheckAccounts, u.id, accId) and
            not self.application.checkMembershipByKitty(cur, u.id, accId)
            ):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.sql.account_movements(accId, int(fromIdx), int(toIdx)))
        return list(cur)

class AccountAmountHandler (JsonBaseHandler):
    def do (self, cur, accId):
        u = self.get_logged_user()
        if (not self.application.hasAccount(cur, u.id, accId) and
            not self.application.hasPermissionByAccount(cur, sql.P_canCheckAccounts, u.id, accId) and
            not self.application.checkMembershipByKitty(cur, u.id, accId)
            ):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.sql.account_amount(accId))
        v = cur.fetchone()
        return v[0] or 0.0, v[1]

class CsaInfoHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.get_logged_user()
        if not self.application.hasPermissionByCsa(cur, sql.P_membership, u.id, csaId):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.sql.csa_info(csaId))
        r = sql.fetch_object(cur)
        cur.execute(*self.application.sql.csa_account(csaId, self.application.sql.At_Kitty, full=True))
        r['kitty'] = sql.fetch_object(cur)
        cur.execute(*self.application.sql.csa_last_kitty_deposit(r['kitty']['id']))
        r['last_kitty_deposit'] = sql.fetch_object(cur)
        return r

class CsaListHandler (JsonBaseHandler):
    def do (self, cur):
        u = self.get_logged_user()
        cur.execute(*self.application.sql.csa_list(u.id))
        return self.application.sql.iter_objects(cur)

class CsaChargeMembershipFeeHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.get_logged_user()
        if not self.application.hasPermissionByCsa(cur, sql.P_canEditMembershipFee, u.id, csaId):
            raise Exception(error_codes.E_permission_denied)

        p = self.payload
        tDesc = p['description']
        amount = p['amount']
        kittyId = p['kitty']
        if amount < 0:
            raise Exception(error_codes.E_illegal_payload)
        now = datetime.datetime.utcnow()
        cur.execute(*sql.csa_account(csaId, sql.At_Kitty, accId=kittyId, full=True))
        acc = sql.fetch_object(cur)
        if acc is None:
            raise Exception(error_codes.E_illegal_payload)
        currencyId = acc['currency_id']
        cur.execute(*sql.insert_transaction(tDesc,
                                            now,
                                            sql.Tt_CashExchange,
                                            currencyId,
                                            csaId
                                            )
                    )
        tid = cur.lastrowid
        cur.execute(*sql.insert_transaction_line_membership_fee(tid, amount, csaId, currencyId))
        cur.execute(*sql.complete_cashexchange(tid, kittyId))
        cur.execute(*sql.log_transaction(tid, u.id, sql.Tl_Added, sql.Tn_kitty_deposit, now))
        return { 'tid': tid }

class CsaRequestMembershipHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.get_current_user()
        if self.application.hasPermissionByCsa(cur, sql.P_membership, u, csaId):
            raise Exception(error_codes.E_already_member)
        profiles, contacts, args = self.application.sql.people_profiles1([u])
        cur.execute(profiles, args)
        profile = self.application.sql.fetch_object(cur)
        cur.execute(contacts, args)
        contacts = list( self.application.sql.iter_objects(cur) )

        self.notify(
            'membership_request',
            profile = profile,
            contacts = contacts
        )

class CsaDeliveryPlacesHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.get_current_user()
        if not self.application.hasPermissionByCsa(cur, sql.P_membership, u, csaId):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.sql.csa_delivery_places(csaId))
        return self.application.sql.iter_objects(cur)

class AccountXlsHandler (BaseHandler):
    def get (self, accId):
        u = self.get_logged_user()
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/vnd.ms-excel')
        self.clear_header('Content-Disposition')
        self.add_header('Content-Disposition', 'attachment; filename="account-%s.xls"' % accId)
        with self.application.conn as cur:
            if (not self.application.hasAccount(cur, u.id, accId) and
                not self.application.hasPermissionByAccount(cur, sql.P_canCheckAccounts, u.id, accId) and
                not self.application.checkMembershipByKitty(cur, u.id, accId)
                ):
                raise HTTPError(403)
            style = xlwt.XFStyle()
            style.num_format_str='YYYY-MM-DD' # FIXME: i18n
            w = xlwt.Workbook(encoding='utf-8')
            s = w.add_sheet('Conto') # FIXME: correggere e i18n
            cur.execute(*self.application.sql.account_movements(accId, None, None))
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

# lo lascio per futura pagina diagnostica: deve comunque ritornare sempre 0.0
#class CsaAmountHandler (JsonBaseHandler):
#    def do (self, cur, csaId):
#        u = self.get_logged_user()
#        if not self.application.hasPermissionByCsa(cur, sql.P_canCheckAccounts, u.id, csaId):
#            raise Exception(error_codes.E_permission_denied)
#        cur.execute(*self.application.sql.csa_amount(csaId))
#        return cur.fetchone()

# TODO: riprisitnare quando si edita il profilo utente
#class PermissionsHandler (JsonBaseHandler):
#    '''Restituisce tutti i permessi visibili dall'utente loggato.
#    '''
#    def do (self, cur):
#        u = self.application.session(self).get_logged_user('not authenticated')
#        cur.execute(*self.application.sql.find_visible_permissions(u.id))
#        return list(cur)

class ProfileInfoHandler (JsonBaseHandler):
    def do (self, cur):
        u = self.get_logged_user()
        cur.execute(*self.application.sql.find_user_permissions(u.id))
        pp = [ p[0] for p in cur ]
        cur.execute(*self.application.sql.find_user_csa(u.id))
        csa = dict(cur)
        cur.execute(*self.application.sql.find_user_accounts(u.id))
        accs = list(cur)
        return dict(
                logged_user = u,
                permissions = pp,
                csa = csa,
                accounts = accs
                )

class AccountsIndexHandler (JsonBaseHandler):
    def do (self, cur, csaId, fromIdx, toIdx):
        q = '%%%s%%' % self.payload['q']
        o = self.application.sql.accounts_index_order_by[int(self.payload['o'])]
        u = self.get_logged_user()
        if self.application.hasPermissionByCsa(cur, sql.P_canCheckAccounts, u.id, csaId):
            cur.execute(*self.application.sql.accounts_index(csaId, q, o, int(fromIdx), int(toIdx)))
        elif self.application.hasPermissionByCsa(cur, sql.P_canViewContacts, u.id, csaId):
            cur.execute(*self.application.sql.people_index(csaId, q, o, int(fromIdx), int(toIdx)))
        else:
            raise Exception(error_codes.E_permission_denied)
        return list(cur)

class AccountsNamesHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.get_logged_user()
        if not self.application.hasPermissions(cur, sql.editableTransactionPermissions, u.id, csaId):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.sql.account_currencies(csaId))
        accountCurs = list(cur)
        cur.execute(*self.application.sql.account_people(csaId))
        accountPeople = list(cur)
        cur.execute(*self.application.sql.account_people_addresses(csaId))
        accountPeopleAddresses = list(cur)
        cur.execute(*self.application.sql.csa_account(csaId, sql.At_Kitty))
        kitty = [ x[0] for x in cur ]
        return dict(
            accountCurrencies = accountCurs,
            accountPeople = accountPeople,
            accountPeopleAddresses = accountPeopleAddresses,
            kitty = kitty,
            )

class ExpensesNamesHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.get_logged_user()
        if not self.application.hasPermissionByCsa(cur, sql.P_canEnterPayments, u.id, csaId):
            raise Exception(error_codes.E_permission_denied)
        r = {}
        cur.execute(*self.application.sql.expenses_accounts(csaId))
        r['accounts'] = list(cur)
        cur.execute(*self.application.sql.expenses_line_descriptions(csaId))
        r['tags'] = list(cur)
        cur.execute(*self.application.sql.expenses_transaction_descriptions(csaId))
        r['tags'] += [ x[0] for x in cur]
        return r

class TransactionEditHandler (JsonBaseHandler):
    def do (self, cur, csaId, transId):
        u = self.get_logged_user()
        cur.execute(*self.application.sql.transaction_edit(transId))

        r = sql.fetch_struct(cur)
        r['transId'] = transId

        ccType = r['cc_type']
        # regole per editare:
        # è D, ho P_canEnterDeposit e l'ho creata io
        # è P, ho P_canEnterPayments e l'ho creata io
        # oppure P_canManageTransactions
        if (not self.application.hasPermissions(cur, [ sql.P_canManageTransactions, sql.P_canCheckAccounts ], u.id, csaId) and
            not (ccType in self.application.sql.editableTransactions and
                 self.application.hasPermissionByCsa(cur, sql.transactionPermissions.get(ccType), u.id, csaId) and
                 self.application.isTransactionEditor(cur, transId, u.id)
                 ) and
            not self.application.isInvolvedInTransaction(cur, transId, u.id)
            ):
            raise Exception(error_codes.E_permission_denied)
        cur.execute(*self.application.sql.transaction_lines(transId))
        r['lines'] = [ dict(account=l[1], notes=l[2], amount=l[3]) for l in cur]

        accountPeopleIndex = {}
        r['people'] = accountPeopleIndex
        cur.execute(*self.application.sql.transaction_people(transId))
        for accId, personId in cur.fetchall():
            pp = accountPeopleIndex.setdefault(accId, [])
            pp.append(personId)
        cur.execute(*self.application.sql.csa_account(csaId, sql.At_Kitty))
        r['kitty'] = [ x[0] for x in cur ]

        return r

class TransactionSaveHandler (JsonBaseHandler):
    notifyExceptions = True
    def do (self, cur, csaId):
        #involvedAccounts = dict()

        csaId = int(csaId)
        u = self.get_logged_user()
        tdef = self.payload
        transId = tdef.get('transId', None)
        ttype = tdef['cc_type']
        tcurr = tdef['currency']
        tlines = tdef['lines']
        tdate = jsonlib.decode_date(tdef['date'])
        tdesc = tdef['description']
        tlogType = None
        tlogDesc = error_codes.E_ok
        if tdesc is None:
            tdesc = datetime.datetime.utcnow()
        if transId is None:
            oldCc = None
            oldDesc = None
        else:
            transId = int(transId)
            cur.execute(*self.application.sql.transaction_type(transId))
            oldCc, oldDesc, modifiedBy = cur.fetchone()
            if modifiedBy is not None:
                raise Exception(error_codes.E_already_modified)
        if ttype in (self.application.sql.Tt_Deposit, self.application.sql.Tt_CashExchange, self.application.sql.Tt_Withdrawal):
            if oldCc is not None and oldCc != ttype:
                raise Exception(error_codes.E_type_mismatch)
            if len(tlines) == 0:
                raise Exception(error_codes.E_no_lines)
            if ((not self.application.hasPermissionByCsa(cur, sql.transactionPermissions[ttype], u.id, csaId) or
                (transId is not None and not self.application.isTransactionEditor(cur, transId, u.id))) and
                not self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId)):
                raise Exception(error_codes.E_permission_denied)
            if ttype == sql.Tt_CashExchange:
                treceiver = tdef['receiver']
                cur.execute(*self.application.sql.account_currency(treceiver, csaId, tcurr))
                if cur.fetchone()[0] == 0:
                    raise Exception(error_codes.E_illegal_receiver)
                #else:
                #    involvedAccounts['unknown_amount'] = treceiver
            cur.execute(*self.application.sql.insert_transaction(tdesc, tdate, self.application.sql.Tt_Unfinished, tcurr, csaId))
            tid = cur.lastrowid
            if tid == 0:
                raise Exception(error_codes.E_illegal_currency)
            fam = '-' if ttype == self.application.sql.Tt_Withdrawal else ''
            for l in tlines:
                desc = l['notes']
                amount = str(l['amount'])
                accId = l['account']
                if float(amount) <= 0:
                    ttype = self.application.sql.Tt_Error
                    tlogType = self.application.sql.Tl_Error
                    tlogDesc = error_codes.E_negative_amount
                    break
                realAmount = fam + amount
                cur.execute(*self.application.sql.insert_transaction_line(tid, desc, realAmount, accId))
                #involvedAccounts[accId] = realAmount
            if ttype != self.application.sql.Tt_Error:
                cur.execute(*self.application.sql.check_transaction_coherency(tid))
                v = list(cur)
                if len(v) != 1:
                    ttype = self.application.sql.Tt_Error
                    tlogType = self.application.sql.Tl_Error
                    tlogDesc = error_codes.E_accounts_not_omogeneous_for_currency_and_or_csa
                elif v[0][1] != csaId:
                    ttype = self.application.sql.Tt_Error
                    tlogType = self.application.sql.Tl_Error
                    tlogDesc = error_codes.E_accounts_do_not_belong_to_csa
                elif ttype == sql.Tt_CashExchange:
                    cur.execute(*self.application.sql.complete_cashexchange(tid, treceiver))
                    tlogType = self.application.sql.Tl_Added if transId is None else self.application.sql.Tl_Modified
                else:
                    cur.execute(*self.application.sql.complete_deposit_or_withdrawal(
                                tid,
                                csaId,
                                self.application.sql.At_Income
                                 if ttype == self.application.sql.Tt_Deposit
                                 else self.application.sql.At_Expense)
                                )
                    tlogType = self.application.sql.Tl_Added if transId is None else self.application.sql.Tl_Modified
        elif ttype == self.application.sql.Tt_Payment:
            if oldCc is not None and oldCc != ttype:
                raise Exception(error_codes.E_illegal_update)
            if len(tlines) == 0:
                raise Exception(error_codes.E_no_lines)
            if ((not self.application.hasPermissionByCsa(cur, sql.transactionPermissions[ttype], u.id, csaId) or
                (transId is not None and not self.application.isTransactionEditor(cur, transId, u.id))) and
                not self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId)):
                raise Exception(error_codes.E_permission_denied)
            cur.execute(*self.application.sql.insert_transaction(tdesc, tdate, self.application.sql.Tt_Unfinished, tcurr, csaId))
            tid = cur.lastrowid
            if tid == 0:
                raise Exception(error_codes.E_illegal_currency)
            # calcolo il conto spese
            cur.execute(*self.application.sql.csa_account(csaId, 'EXPENSE', tcurr))
            expenseAccountId = cur.fetchone()[0]
            for l in tlines:
                desc = l['notes']
                amount = l['amount']
                accId = l['account'] or expenseAccountId # qui assumo che account id non sia zero!
                cur.execute(*self.application.sql.insert_transaction_line(tid, desc, amount, accId))
                lastLineId = cur.lastrowid
                #lastAccId = accId
                #involvedAccounts[accId] = amount
            cur.execute(*self.application.sql.check_transaction_coherency(tid))
            v = list(cur)
            if len(v) != 1:
                ttype = self.application.sql.Tt_Error
                tlogType = self.application.sql.Tl_Error
                tlogDesc = error_codes.E_accounts_not_omogeneous_for_currency_and_or_csa
            elif v[0][1] != csaId:
                ttype = self.application.sql.Tt_Error
                tlogType = self.application.sql.Tl_Error
                tlogDesc = error_codes.E_accounts_do_not_belong_to_csa
            else:
                cur.execute(*self.application.sql.transaction_calc_last_line_amount(tid, lastLineId))
                a = cur.fetchone()[0]
                #involvedAccounts[lastAccId] = str(a)
                cur.execute(*self.application.sql.transaction_fix_amount(lastLineId, a))
                tlogType = self.application.sql.Tl_Added if transId is None else self.application.sql.Tl_Modified
        elif ttype == self.application.sql.Tt_Trashed:
            if oldCc not in self.application.sql.deletableTransactions:
                raise Exception(error_codes.E_illegal_update)
            if len(tlines) > 0:
                raise Exception(error_codes.E_trashed_transactions_can_not_have_lines)
            if transId is None:
                raise Exception(error_codes.E_missing_trashId_of_transaction_to_be_deleted)
            if ((not self.application.hasPermissions(cur, sql.editableTransactionPermissions, u.id, csaId) or
                not self.application.isTransactionEditor(cur, transId, u.id)) and
                not self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId)):
                raise Exception(error_codes.E_permission_denied)
            cur.execute(*self.application.sql.insert_transaction(tdesc, tdate, self.application.sql.Tt_Unfinished, tcurr, csaId))
            tid = cur.lastrowid
            if tid == 0:
                raise Exception(error_codes.E_illegal_currency)
            tlogType = self.application.sql.Tl_Deleted
            #tlogDesc = ''
        else:
            log_gassman.error('illegal transaction type: %s', tdef)
            raise Exception(error_codes.E_illegal_transaction_type)
        cur.execute(*self.application.sql.finalize_transaction(tid, ttype))
        cur.execute(*self.application.sql.log_transaction(tid, u.id, tlogType, tlogDesc, datetime.datetime.utcnow()))
        if transId is not None and ttype != self.application.sql.Tt_Error:
            cur.execute(*self.application.sql.update_transaction(transId, tid))
        if ttype == self.application.sql.Tt_Error:
            raise Exception(tlogDesc)
        else:
            self.notifyAccountChange(cur, tid, tdesc, tdate, transId, oldDesc)
        return tid

    # Transaction notification types
    Tnt_new_transaction = 'n'
    Tnt_amount_changed = 'a'
    Tnt_notes_changed = 'd'
    Tnt_transaction_removed = 'r'
    Tnt_description_changed = 'm'

    def notifyAccountChange (self, cur, transId, tdesc, tdate, modifiedTransId, oldDesc):
        cur.execute(*sql.transaction_fetch_lines_to_compare(modifiedTransId, transId))
        oldLines = dict()
        newLines = dict()
        diffs = dict()
        lines = {
            transId: newLines,
            modifiedTransId: oldLines,
        }
        for trans, accId, amount, lineDesc in cur.fetchall():
            lines[trans][accId] = (amount, lineDesc)
        for acc, newp in newLines.items():
            oldp = oldLines.get(acc)
            if oldp is None:
                diffs[accId] = [ self.Tnt_new_transaction ]
            elif oldp[0] != newp[0]:
                diffs[accId] = [ self.Tnt_amount_changed, newp[0], oldp[0] ]
            elif oldp[1] != newp[1]:
                diffs[accId] = [ self.Tnt_notes_changed, newp[1], oldp[1] ]
        for acc, oldp in oldLines.items():
            newp = newLines.get(acc)
            if newp is None:
                diffs[accId] = [ self.Tnt_transaction_removed ]
            #elif oldp[0] != newp[0]:
            #    diffs[accId] = ... Tnt_amount_changed
            #elif oldp[1] != newp[1]:
            #    diffs[accId] = ... Tnt_notes_changed
        if modifiedTransId is not None and tdesc != oldDesc:
            for acc in newLines:
                if acc not in diffs:
                    diffs[acc] = [ self.Tnt_description_changed, tdesc, oldDesc ]
        if len(diffs) == 0:
            log_gassman.debug('nothing to notify for transaction %s modifying transaction %s', transId, modifiedTransId)
            return
        # FIXME: soglia specifica di csa
        LVL_THRES = -40
        #signalledPeople = dict() # da persone (pid) a lista di account ([accountId])
        accounts = dict() # da account (accountId) a lista di persone ([{first/middle/last_name, email}])
        # considero solo gli account i cui owner hanno nei settaggi la ricezione di ogni notifica
        cur.execute(*sql.account_email_for_notifications(diffs.keys()))
        for accId, pid, first_name, middle_name, last_name, email in cur.fetchall():
            #signalledPeople.setdefault(pid, []).append(accId)
            accounts.setdefault(
                accId,
                {}
            ).setdefault(
                'people',
                []
            ).append(dict(
                first_name = first_name,
                middle_name = middle_name,
                last_name = last_name,
                email = email
            ))
        if len(accounts) == 0:
            log_gassman.info('involved accounts has no mail to notify to')
            return
        cur.execute(*sql.account_total_for_notifications(accounts.keys()))
        for accId, total, currSym in cur.fetchall():
            accounts[accId]['account'] = (total, currSym)
        for accId, accData in accounts.items():
            total, currSym = accData['account']
            people = accData['people']
            notificationType = diffs[accId]
            # TODO: Localizzazione del messaggio
            self.notify(
                'account_update',
                total = total,
                currency = currSym,
                threshold = LVL_THRES,
                people = people,
                tdesc = tdesc,
                tdate = tdate,
                dateFormatter = shortDate,
                accId = accId,
                transId = transId,
                modifiedTransId = modifiedTransId,
                oldDesc = oldDesc,
                notificationType = notificationType,
                Tnt_new_transaction = self.Tnt_new_transaction,
                Tnt_amount_changed = self.Tnt_amount_changed,
                Tnt_notes_changed = self.Tnt_notes_changed,
                Tnt_transaction_removed = self.Tnt_transaction_removed,
                Tnt_description_changed = self.Tnt_description_changed,
            )

class TransactionsEditableHandler (JsonBaseHandler):
    def do (self, cur, csaId, fromIdx, toIdx):
        q = '%%%s%%' % self.payload['q']
        o = self.application.sql.transactions_editable_order_by[int(self.payload['o'])]
        u = self.get_logged_user()
        if self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId):
            cur.execute(*self.application.sql.transactions_all(csaId, q, o, int(fromIdx), int(toIdx)))
        elif self.application.hasPermissions(cur, sql.editableTransactionPermissions, u.id, csaId):
            cur.execute(*self.application.sql.transactions_by_editor(csaId, u, q, o, int(fromIdx), int(toIdx)))
        else:
            raise Exception(error_codes.E_permission_denied)
        return list(cur)

def shortDate (d):
    return d.strftime('%Y/%m/%d') # FIXME il formato dipende dal locale dell'utente

def pubDate (d):
    return d.strftime('%a, %d %b %Y %H:%M:%S GMT')

def currency (v, sym):
    return '%s%s' % (v, sym)

class RssFeedHandler (tornado.web.RequestHandler):
    def get (self, rssId):
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
    def do (self, cur, csaId):
        pids = self.payload['pids']
        u = self.get_logged_user()
        isSelf = len(pids) == 1 and int(pids[0]) == u.id
        if csaId == 'null':
            if not isSelf:
                raise Exception(error_codes.E_permission_denied)
            csaId = None
        if not isSelf and not self.application.hasPermissionByCsa(cur, sql.P_membership, u.id, csaId):
            raise Exception(error_codes.E_permission_denied)
        canViewContacts = isSelf or self.application.hasPermissionByCsa(cur, sql.P_canViewContacts, u.id, csaId)
        r = {}
        if len(pids) == 0:
            return r
        def record (pid):
            p = r.get(pid, None)
            if p is None:
                p = { 'accounts':[], 'profile':None, 'permissions':[], 'contacts':[] }
                r[pid] = p
            return p
        if csaId is None:
            r[u.id] = record(u.id)
        else:
            accs, perms, args = self.application.sql.people_profiles2(csaId, pids)
            if isSelf or self.application.hasPermissionByCsa(cur, sql.P_canCheckAccounts, u.id, csaId):
                cur.execute(accs, args)
                for acc in self.application.sql.iter_objects(cur):
                    p = record(acc['person_id'])
                    p['accounts'].append(acc)
            cur.execute(perms, args)
            for perm in self.application.sql.iter_objects(cur):
                p = record(perm['person_id'])
                if canViewContacts:
                    p['permissions'].append(perm['perm_id'])
        if r.keys():
            profiles, contacts, args = self.application.sql.people_profiles1(r.keys())
            cur.execute(profiles, args)
            for prof in self.application.sql.iter_objects(cur):
                p = record(prof['id'])
                p['profile'] = prof
            if canViewContacts:
                cur.execute(contacts, args)
                for addr in self.application.sql.iter_objects(cur):
                    p = record(addr['person_id'])
                    p['contacts'].append(addr)
            # TODO: indirizzi
        return r

class PersonSaveHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.get_logged_user()
        p = self.payload
        log_gassman.debug('saving: %s', p)
        profile = p['profile']
        pid = int(profile['id'])
        if csaId == 'null':
            if pid != u.id:
                raise Exception(error_codes.E_permission_denied)
            csaId = None
        elif (
            (not self.application.hasPermissionByCsa(cur, sql.P_canEditContacts, u.id, csaId) and
             u.id != pid
             ) or \
            not self.application.hasPermissionByCsa(cur, sql.P_membership, pid, csaId)
            ):
            raise Exception(error_codes.E_permission_denied)
        # salva profilo
        cur.execute(*self.application.sql.updateProfile(profile))
        # salva contatti
        contacts = p['contacts']
        cur.execute(*self.application.sql.fetchContacts(pid))
        ocontacts = [ x[0] for x in cur.fetchall() ]
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
        if csaId is not None and self.application.hasPermissionByCsa(cur, sql.P_canGrantPermissions, u.id, csaId):
            cur.execute(*self.application.sql.permissionLevel(pid, csaId))
            ulevel = cur.fetchone()[0]
            permissions = p['permissions']
            cur.execute(*self.application.sql.revokePermissions(pid, csaId, ulevel))
            for p in permissions:
                if p < ulevel:
                    cur.execute(*self.application.sql.grantPermission(pid, p, csaId))
        # TODO: salva indirizzi
        fee = p.get('membership_fee')
        if csaId is not None and fee and self.application.hasPermissionByCsa(cur, sql.P_canEditMembershipFee, u.id, csaId):
            #accId = fee.get('account')
            amount = fee.get('amount')
            if float(amount) >= 0:
                cur.execute(*self.application.sql.account_updateMembershipFee(csaId, pid, amount))

class PersonCheckEmailHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.get_logged_user()
        p = self.payload
        log_gassman.debug('saving: %s', p)
        pid = p['id']
        email = p['email']
        if (
            (not self.application.hasPermissionByCsa(cur, sql.P_canEditContacts, u.id, csaId) and
             u.id != int(pid)
             ) or \
            not self.application.hasPermissionByCsa(cur, sql.P_membership, pid, csaId)
            ):
            raise Exception(error_codes.E_permission_denied)
        # verifica unicità
        cur.execute(*self.application.sql.isUniqueEmail(pid, email))
        return cur.fetchone()[0]

if __name__ == '__main__':
    io_loop = tornado.ioloop.IOLoop.instance()

    tornado.locale.load_translations(settings.TRANSLATIONS_PATH)

    mailer = asyncsmtp.Mailer(settings.SMTP_SERVER,
                              settings.SMTP_PORT,
                              settings.SMTP_NUM_THREADS,
                              settings.SMTP_QUEUE_TIMEOUT,
                              io_loop
                              ) if settings.SMTP_SERVER else None

    connArgs = dict(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    passwd=settings.DB_PASSWORD,
                    db=settings.DB_NAME,
                    charset='utf8'
                    )

    application = GassmanWebApp(sql,
                                mailer,
                                connArgs
                                )
    application.listen(settings.HTTP_PORT)

    log_gassman.info('GASsMAN web server up and running...')

    io_loop.start()
