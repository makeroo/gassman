#!/usr/local/bin/python3
# encoding=utf-8

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
import tornado.escape

import gassman_settings as settings
import gassman_version
import jsonlib
import pymysql
import sql
import loglib
import smtplib

logging.config.dictConfig(settings.LOG)

log_gassman = logging.getLogger('gassman.application')

# TODO: db asincrono

def rss_feed_id (pid):
    return hashlib.sha256((settings.COOKIE_SECRET + str(pid)).encode('utf-8')).hexdigest()

class GoogleUser (object):
    authenticator = 'Google'

    def __init__ (self, userInfo):
        self.userId = userInfo['claimed_id']
        self.firstName = userInfo.get('first_name', '')
        self.middleName = None
        self.lastName = userInfo.get('last_name', '')
        self.email = userInfo.get('email', '')

class Session (object):
    def __init__ (self, app):
        self.application = app
        self.logged_user = None
        self.created = datetime.datetime.utcnow()
        self.registrationNotificationSent = False

    def get_logged_user (self, error='not authenticated'):
        if not self.logged_user:
            if error:
                raise Exception(error)
            else:
                return None
#        if self.logged_user.account is None:
#            # controllo per vedere se è avvenuta la registrazione
#            with self.application.conn as cur:
#                cur.execute(*self.application.sql.find_current_account(self.logged_user.id))
#                try:
#                    self.logged_user.account = int(cur.fetchone()[0])
#                except:
#                    etype, evalue, _ = sys.exc_info()
#                    log_gassman.debug('account not found: user=%s, cause=%s/%s', self.logged_user.id, etype, evalue)
        return self.logged_user

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
    def __init__ (self, sql, **connArgs):
        handlers = [
            (r'^/$', IndexHandler),
            (r'^/login.html$', LoginHandler),
            (r'^/home.html$', HomeHandler),
            (r'^/auth/google$', GoogleAuthLoginHandler),
            (r'^/incomplete_profile.html$', IncompleteProfileHandler),
            (r'^/sys/version$', SysVersionHandler),
#            (r'^/account/movements/(\d+)/(\d+)$', SelfAccountMovementsHandler),
            (r'^/account/(\d+)/owner$', AccountOwnerHandler),
            (r'^/account/(\d+)/movements/(\d+)/(\d+)$', AccountMovementsHandler),
            (r'^/account/(\d+)/amount$', AccountAmountHandler),
            (r'^/profile-info$', ProfileInfoHandler),
            (r'^/accounts/(\d+)/index/(\d+)/(\d+)$', AccountsIndexHandler),
            (r'^/accounts/(\d+)/names$', AccountsNamesHandler),
            (r'^/transaction/(\d+)/(\d+)/detail$', TransactionDetailHandler),
            (r'^/transaction/(\d+)/(\d+)/edit$', TransactionEditHandler),
            (r'^/transaction/(\d+)/save$', TransactionSaveHandler),
            (r'^/transactions/(\d+)/editable/(\d+)/(\d+)$', TransactionsEditableHandler),
            (r'^/csa/(\d+)/total_amount$', CsaAmountHandler),
            (r'^/rss/(.+)$', RssFeedHandler),
            ]
        codeHome = os.path.dirname(__file__)
        sett = dict(
            cookie_secret = settings.COOKIE_SECRET,
            template_path = os.path.join(codeHome, 'templates'),
            static_path = os.path.join(codeHome, "static"),
            xsrf_cookies = True,
            login_url = '/login.html',
            )
        super().__init__(handlers, **sett)
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
            self.notify('FATAL', 'No db connection', 'Connection error: %s/%s.\nTraceback:\n%s' %
                           (etype, evalue, loglib.TracebackFormatter(tb))
                           )

    def notify (self, level, subject, body):
        if settings.SMTP_SERVER is None:
            log_gassman.info('SMTP not configured, mail not sent: %s / %s', subject, body)
            return
        try:
            smtp = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            smtp.sendmail(settings.SMTP_SENDER, settings.SMTP_RECEIVER,
                          'Subject: [GASsMan] %s %s\n\n%s' % (level, subject, body))
            smtp.quit()
            return True
        except:
            etype, evalue, tb = sys.exc_info()
            log_gassman.error('can\'t send mail: subject=%s, cause=%s/%s', subject, etype, evalue)
            log_gassman.debug('email body: %s', body)
            log_gassman.debug('full stacktrace:\n%s', loglib.TracebackFormatter(tb))
            return False

    def hasAccounts (self, pid):
        with self.conn as cur:
            cur.execute(*self.sql.has_accounts(pid))
            return cur.fetchone()[0] > 0

    def hasAccount (self, cur, pid, accId):
        cur.execute(*self.sql.has_account(pid, accId))
        return cur.fetchone()[0] > 0

    def checkProfile (self, requestHandler, user):
        with self.conn as cur:
            cur.execute(*self.sql.check_user(user.userId, user.authenticator))
            try:
                pp = list(cur)
                if len(pp) == 0:
                    raise Person.DoesNotExist
                p = Person(*pp[0])
                if len(pp) > 1:
                    self.notify('ERROR', 'Multiple auth id for %s' % p, 'Check auth id %s' % user.userId)
                log_gassman.debug('found profile: authId=%s, person=%s', user.userId, p)
            except Person.DoesNotExist:
                try:
                    # non ho trovato niente su db
                    cur.execute(*self.sql.create_contact(user.userId, self.sql.Ck_Id, user.authenticator))
                    contactId = cur.lastrowid
                    cur.execute(*self.sql.create_person(user.firstName, user.middleName, user.lastName))
                    p_id = cur.lastrowid
                    rfi = rss_feed_id(p_id)
                    cur.execute(*self.sql.assign_rss_feed_id(p_id, rfi))
                    cur.execute(*self.sql.assign_contact(contactId, p_id))
                    if user.email:
                        cur.execute(*self.sql.create_contact(user.email, self.sql.Ck_Email, ''))
                        emailId = cur.lastrowid
                        cur.execute(*self.sql.assign_contact(emailId, p_id))
                    p = Person(p_id, user.firstName, user.middleName, user.lastName, rfi)
                    log_gassman.info('profile created: newUser=%s', p)
                except:
                    etype, evalue, tb = sys.exc_info()
                    log_gassman.error('profile creation failed: cause=%s/%s\nfull stacktrace:\n%s', etype, evalue, loglib.TracebackFormatter(tb))
                    self.notify('ERROR', 'User profile creation failed', 'Cause: %s/%s\nAuthId: %s (%s %s)\nTraceback:\n%s' %
                                   (etype, evalue, user.userId, user.firstName, user.lastName, loglib.TracebackFormatter(tb))
                                   )
                    return None
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
                        log_gassman.info('created session: token=%s, user=%s', xt, s.logged_user)
                    else:
                        log_gassman.warning('created session, user not found: token=%s, pid=%s', xt, pid)
            else:
                log_gassman.info('created session: token=%s', xt)
        return s

    def hasPermissionByAccount (self, cur, perm, personId, accId):
        cur.execute(*self.sql.has_permission_by_account(perm, personId, accId))
        r = int(cur.fetchone()[0]) > 0
        log_gassman.debug('has permission: user=%s, perm=%s, r=%s', personId, perm, r)
        return r

    def hasPermissionByCsa (self, cur, perm, personId, csaId):
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

class BaseHandler (tornado.web.RequestHandler):
    def get_current_user (self):
        c = self.get_secure_cookie('user', max_age_days=settings.COOKIE_MAX_AGE_DAYS)
        return int(c) if c else None

class IndexHandler (BaseHandler):
    def get (self):
        p = self.application.session(self).get_logged_user(None)
        if p is None:
            self.redirect("/login.html")
        elif self.application.hasAccounts(p.id):
            self.redirect("/home.html")
        else:
            self.redirect("/incomplete_profile.html")

class LoginHandler (BaseHandler):
    def get (self):
        p = self.application.session(self).get_logged_user(None)
        if p is None:
            self.render('login.html')
        elif self.application.hasAccounts(p.id):
            self.redirect("/home.html")
        else:
            self.redirect("/incomplete_profile.html")

class IncompleteProfileHandler (tornado.web.RequestHandler):
    def get (self):
        s = self.application.session(self)
        p = s.get_logged_user(None)
        if not p or self.application.hasAccounts(p.id):
            self.redirect('/')
        elif not s.registrationNotificationSent:
            s.registrationNotificationSent = self.application.notify('INFO',
                                                                     'Complete registration for %s %s' %
                                                                     (p.firstName, p.lastName),
                                                                     'User without account: %s' % p)
            self.render('incomplete_profile.html')

#class GoogleAuthLoginHandler2 (tornado.web.RequestHandler, tornado.auth.GoogleOAuth2Mixin):
#    @tornado.gen.coroutine
#    def get (self):
#        if self.get_argument('code', False):
#            user = yield self.get_authenticated_user(
#                redirect_uri='http://your.site.com/auth/google',
#                code=self.get_argument('code'))
#            # Save the user with e.g. set_secure_cookie
#            log_gassman.debug('user received: %s', user)
#            self.redirect("/home.html")
#        else:
#            yield self.authorize_redirect(
#                redirect_uri='http://localhost:8180/auth/google',
#                client_id=self.settings['google_oauth']['key'],
#                scope=['profile', 'email'],
#                response_type='code',
#                extra_params={'approval_prompt': 'auto'})

class GoogleAuthLoginHandler (tornado.web.RequestHandler, tornado.auth.GoogleMixin):
    @tornado.gen.coroutine
    def get (self):
        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            #log_gassman.debug('user received: %s', user)
            person = self.application.checkProfile(self, GoogleUser(user))
            self.application.session(self).logged_user = person
            if self.application.hasAccounts(person.id):
                self.redirect("/home.html")
            else:
                self.redirect("/incomplete_profile.html")
        else:
            self.authenticate_redirect(ax_attrs=["name", "email"])

# TODO: facebook login

# TODO: twitter login

class HomeHandler (BaseHandler):
    @tornado.web.authenticated
    def get (self):
        u = self.application.session(self).get_logged_user('not authenticated')
        with self.application.conn as cur:
            cur.execute(*self.application.sql.rss_id(u.id))
        self.render('home.html',
                    rssId=cur.fetchone()[0],
                    MINIFIED=settings.MINIFIED)

class JsonBaseHandler (BaseHandler):
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
        etype, evalue, _ = kwargs.get('exc_info', ('', '', None))
        if hasattr(evalue, 'args'):
            i = [ str(etype) ] + list(evalue.args)
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
                raise Exception('illegal payload')
        return self._payload

class SysVersionHandler (JsonBaseHandler):
    def post (self):
        data = [ gassman_version.version ]
        self.write_response(data)

#class SelfAccountMovementsHandler (JsonBaseHandler):
#    def post (self, fromIdx, toIdx):
#        a = self.application.session(self).get_logged_user('not authenticated').account
#        self.fetchMovements(a, fromIdx, toIdx)

class AccountOwnerHandler (JsonBaseHandler):
    def do (self, cur, accId):
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasAccount(cur, u.id, accId) and not self.application.hasPermissionByAccount(cur, sql.P_canCheckAccounts, u.id, accId):
            raise Exception('permission denied')
        cur.execute(*self.application.sql.account_owners(accId))
        return list(cur)

class AccountMovementsHandler (JsonBaseHandler):
    def do (self, cur, accId, fromIdx, toIdx):
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasAccount(cur, u.id, accId) and not self.application.hasPermissionByAccount(cur, sql.P_canCheckAccounts, u.id, accId):
            raise Exception('permission denied')
        cur.execute(*self.application.sql.account_movements(accId, int(fromIdx), int(toIdx)))
        return list(cur)

class AccountAmountHandler (JsonBaseHandler):
    def do (self, cur, accId):
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasAccount(cur, u.id, accId) and not self.application.hasPermissionByAccount(cur, sql.P_canCheckAccounts, u.id, accId):
            raise Exception('permission denied')
        cur.execute(*self.application.sql.account_amount(accId))
        return cur.fetchone()

class CsaAmountHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasPermissionByCsa(cur, sql.P_canCheckAccounts, u.id, csaId):
            raise Exception('permission denied')
        cur.execute(*self.application.sql.csa_amount(csaId))
        return cur.fetchone()

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
        u = self.application.session(self).get_logged_user('not authenticated')
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
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasPermissionByCsa(cur, sql.P_canCheckAccounts, u.id, csaId):
            raise Exception('permission denied')
        cur.execute(*self.application.sql.accounts_index(csaId, int(fromIdx), int(toIdx)))
        return list(cur)

class AccountsNamesHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasPermissions(cur, [sql.P_canEnterDeposit, sql.P_canEnterPayments], u.id, csaId):
            raise Exception('permission denied')
        cur.execute(*self.application.sql.account_names(csaId))
        accountNames = list(cur)
        cur.execute(*self.application.sql.account_people(csaId))
        accountPeople = list(cur)
        cur.execute(*self.application.sql.account_people_addresses(csaId))
        accountPeopleAddresses = list(cur)
        return dict(
            accountNames = accountNames,
            accountPeople = accountPeople,
            accountPeopleAddresses = accountPeopleAddresses
            )

class TransactionDetailHandler (JsonBaseHandler):
    def do (self, cur, csaId, tid):
        # restituisco:
        # lines: [ id, desc, amount, accId ]
        # people: [ id, first, middle, last, accId ]
        # accounts: [ id, gc_name, currency ]
        u = self.application.session(self).get_logged_user('not authenticated')
        cur.execute(*self.application.sql.transaction_lines(tid))
        lines = list(cur)
        cur.execute(*self.application.sql.transaction_people(tid))
        people = dict([ (c[4], c) for c in cur])
        if not u.id in [c[0] for c in people.values()] and \
            not self.application.hasPermissionByCsa(cur, sql.P_canCheckAccounts, u.id, csaId):
            raise Exception('permission denied')
        cur.execute(*self.application.sql.transaction_account_gc_names(tid))
        accs = dict([( c[0], (c[1], c[2])) for c in cur])
        return dict(
                    lines = lines,
                    people = people,
                    accounts = accs,
                    )

class TransactionEditHandler (JsonBaseHandler):
    def do (self, cur, csaId, transId):
        u = self.application.session(self).get_logged_user('not authenticated')
        cur.execute(*self.application.sql.transaction_edit(transId))
        d = cur.fetchone()
        if d[5] is not None:
            raise Exception('already modified', d[5])
        r = dict(
            transId = transId,
            description = d[0],
            date = d[1],
            cc_type = d[2],
            currency = [ d[3], d[4] ]
            )
        # regole per editare:
        # è D, ho P_canEnterDeposit e l'ho creata io
        # è P, ho P_canEnterPayments e l'ho creata io
        # oppure P_canManageTransactions
        if (not not self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId) and
            not (d[2] in (self.application.sql.Tt_Deposit, self.application.sql.Tt_Payment) and
                 self.application.hasPermissionByCsa(cur, sql.P_canEnterDeposit if d[2] == self.application.sql.Tt_Deposit else sql.P_canEnterPayments, u.id, csaId) and
                 self.application.isTransactionEditor(cur, transId, u.id))
            ):
            raise Exception('permission denied')
        cur.execute(*self.application.sql.transaction_lines(transId))
        r['lines'] = [ dict(account=l[1], notes=l[2], amount=l[3]) for l in cur]
        return r

class TransactionSaveHandler (JsonBaseHandler):
    def do (self, cur, csaId):
        csaId = int(csaId)
        u = self.application.session(self).get_logged_user('not authenticated')
        tdef = self.payload
        transId = tdef.get('transId', None)
        ttype = tdef['cc_type']
        tcurr = tdef['currency']
        tlines = tdef['lines']
        tdate = jsonlib.decode_date(tdef['date'])
        tdesc = tdef['description']
        tlogType = None
        tlogDesc = ''
        if transId is None:
            oldCc = None
        else:
            cur.execute(*self.application.sql.transaction_type(transId))
            oldCc, modifiedBy = cur.fetchone()
            if modifiedBy is not None:
                raise Exception('already modified')
        if ttype == self.application.sql.Tt_Deposit:
            if oldCc is not None and oldCc != self.application.sql.Tt_Deposit:
                raise Exception('type mismatch')
            if len(tlines) == 0:
                raise Exception('no lines')
            if ((not self.application.hasPermissionByCsa(cur, sql.P_canEnterDeposit, u.id, csaId) or
                (transId is not None and not self.application.isTransactionEditor(cur, transId, u.id))) and
                not self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId)):
                raise Exception('permission denied')
            cur.execute(*self.application.sql.insert_transaction(tdesc, tdate, self.application.sql.Tt_Unfinished, tcurr, csaId))
            tid = cur.lastrowid
            if tid == 0:
                raise Exception('illegal currency')
            for l in tlines:
                desc = l['notes']
                amount = l['amount']
                accId = l['account']
                if amount <= 0:
                    ttype = self.application.sql.Tt_Error
                    tlogType = self.application.sql.Tl_Error
                    tlogDesc = 'negative amount'
                    break
                cur.execute(*self.application.sql.insert_transaction_line(tid, desc, amount, accId))
            if ttype != self.application.sql.Tt_Error:
                cur.execute(*self.application.sql.check_transaction_coherency(tid))
                v = list(cur)
                if len(v) != 1:
                    ttype = self.application.sql.Tt_Error
                    tlogType = self.application.sql.Tl_Error
                    tlogDesc = 'accounts not omogeneous for currency and/or csa'
                elif v[0][1] != csaId:
                    ttype = self.application.sql.Tt_Error
                    tlogType = self.application.sql.Tl_Error
                    tlogDesc = 'accounts do not belong to csa'
                else:
                    cur.execute(*self.application.sql.complete_deposit(tid, csaId))
                    tlogType = self.application.sql.Tl_Added if transId is None else self.application.sql.Tl_Modified
        elif ttype == self.application.sql.Tt_Payment:
            if oldCc is not None and oldCc != self.application.sql.Tt_Payment:
                raise Exception('illegal update')
            if len(tlines) == 0:
                raise Exception('no lines')
            if ((not self.application.hasPermissionByCsa(cur, sql.P_canEnterPayments, u.id, csaId) or
                (transId is not None and not self.application.isTransactionEditor(cur, transId, u.id))) and
                not self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId)):
                raise Exception('permission denied')
            cur.execute(*self.application.sql.insert_transaction(tdesc, tdate, self.application.sql.Tt_Unfinished, tcurr, csaId))
            tid = cur.lastrowid
            if tid == 0:
                raise Exception('illegal currency')
            for l in tlines:
                desc = l['notes']
                amount = l['amount']
                accId = l['account']
                cur.execute(*self.application.sql.insert_transaction_line(tid, desc, amount, accId))
                lastLineId = cur.lastrowid
            cur.execute(*self.application.sql.check_transaction_coherency(tid))
            v = list(cur)
            if len(v) != 1:
                ttype = self.application.sql.Tt_Error
                tlogType = self.application.sql.Tl_Error
                tlogDesc = 'accounts not omogeneous for currency and/or csa'
            elif v[0][1] != csaId:
                ttype = self.application.sql.Tt_Error
                tlogType = self.application.sql.Tl_Error
                tlogDesc = 'accounts do not belong to csa'
            else:
                cur.execute(*self.application.sql.transaction_calc_last_line_amount(tid, lastLineId))
                a = cur.fetchone()[0]
                cur.execute(*self.application.sql.transaction_fix_amount(lastLineId, a))
                tlogType = self.application.sql.Tl_Added if transId is None else self.application.sql.Tl_Modified
        elif ttype == self.application.sql.Tt_Trashed:
            if oldCc not in (self.application.sql.Tt_Deposit, self.application.sql.Tt_Payment, self.application.sql.Tt_Generic):
                raise Exception('illegal update')
            if len(tlines) == 0:
                raise Exception('trashed transactions can not have lines')
            if transId is None:
                raise Exception('missing trashId of transaction to be deleted')
            if ((not self.application.hasPermissions(cur, [sql.P_canEnterDeposit, sql.P_canEnterPayments], u.id, csaId) or
                not self.application.isTransactionEditor(cur, transId, u.id)) and
                not self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId)):
                raise Exception('permission denied')
            tlogType = self.application.sql.Tl_Deleted
            #tlogDesc = ''
        else:
            log_gassman.error('illegal transaction type: %s', tdef)
            raise Exception('illegal transaction type')
        cur.execute(*self.application.sql.finalize_transaction(tid, ttype))
        cur.execute(*self.application.sql.log_transaction(tid, u.id, tlogType, tlogDesc, datetime.datetime.utcnow()))
        if transId is not None and ttype != self.application.sql.Tt_Error:
            cur.execute(*self.application.sql.update_transaction(transId, tid))

class TransactionsEditableHandler (JsonBaseHandler):
    def do (self, cur, csaId, fromIdx, toIdx):
        u = self.application.session(self).get_logged_user('not authenticated')
        if self.application.hasPermissionByCsa(cur, sql.P_canManageTransactions, u.id, csaId):
            cur.execute(*self.application.sql.transactions_all(csaId, int(fromIdx), int(toIdx)))
        elif self.application.hasPermissions(cur, [sql.P_canEnterDeposit, sql.P_canEnterPayments], u.id, csaId):
            cur.execute(*self.application.sql.transactions_by_editor(csaId, u, int(fromIdx), int(toIdx)))
        else:
            raise Exception('permission denied')
        return list(cur)


# TODO: ripristinare se si fa la pagina di associazione conto
#class IncompleteProfilesHandler (JsonBaseHandler):
#    '''
#    Restituisce le persone senza account.
#    '''
#    def post (self):
#        u = self.application.session(self).get_logged_user('not authenticated')
#        if not self.application.hasPermission(sql.P_canAssignAccounts, u.id):
#            raise Exception('permission denied')
#        with self.application.conn as cur:
#            cur.execute(*self.application.sql.find_users_without_account())
#            pwa = list(cur)
#            data = dict(
#                        users_without_account=pwa
#                        )
#        self.write_response(data)

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


if __name__ == '__main__':
    io_loop = tornado.ioloop.IOLoop.instance()
    application = GassmanWebApp(sql,
                                host=settings.DB_HOST,
                                port=settings.DB_PORT,
                                user=settings.DB_USER,
                                passwd=settings.DB_PASSWORD,
                                db=settings.DB_NAME,
                                charset='utf8')
    application.listen(settings.HTTP_PORT)
    log_gassman.info('GASsMAN web server up and running...')
    io_loop.start()
