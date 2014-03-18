#!/usr/local/bin/python3
# encoding=utf-8

'''
Created on 01/mar/2014

@author: makeroo
'''

import datetime
import logging.config
import os.path
import sys

import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.gen
import tornado.escape

import gassman_settings as settings
import jsonlib
import pymysql
import sql
import loglib
import smtplib

logging.config.dictConfig(settings.LOG)

log_gassman = logging.getLogger('gassman.application')

# TODO: db asincrono

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
        if self.logged_user.account is None:
            # controllo per vedere se è avvenuta la registrazione
            with self.application.conn as cur:
                cur.execute(*self.application.sql.find_current_account(self.logged_user.id))
                try:
                    self.logged_user.account = int(cur.fetchone()[0])
                except:
                    etype, evalue, _ = sys.exc_info()
                    log_gassman.debug('account not found: user=%s, cause=%s/%s', self.logged_user.id, etype, evalue)
        return self.logged_user

class Person (object):
    def __init__ (self, p_id, p_first_name, p_middle_name, p_last_name, p_current_account_id):
        self.id = p_id
        self.firstName = p_first_name
        self.middleName = p_middle_name
        self.lastName = p_last_name
        self.account = p_current_account_id

    def __str__ (self):
        return '%s (%s %s)' % (self.id, self.firstName, self.lastName)

class GassmanWebApp (tornado.web.Application):
    def __init__ (self, sql, **connArgs):
        handlers = [
            (r'^/$', IndexHandler),
            (r'^/faq.html$', FaqHandler),
            (r'^/help.html$', HelpHandler),
            (r'^/project.html$', ProjectHandler),
            (r'^/home.html$', HomeHandler),
            (r'^/auth/google$', GoogleAuthLoginHandler),
            (r'^/incomplete_profile.html$', IncompleteProfileHandler),
            (r'^/account/movements/(\d+)/(\d+)$', SelfAccountMovementsHandler),
            (r'^/account/(\d+)/movements/(\d+)/(\d+)$', AccountMovementsHandler),
            (r'^/account/amount$', AccountAmountHandler),
            (r'^/profile-info$', ProfileInfoHandler),
            (r'^/accounts/index/(\d+)/(\d+)$', AccountsIndexHandler),
            (r'^/transaction/(\d+)/detail$', TransactionDetailHandler),
            ]
        codeHome = os.path.dirname(__file__)
        sett = dict(
            cookie_secret = settings.COOKIE_SECRET,
            template_path = os.path.join(codeHome, 'templates'),
            static_path = os.path.join(codeHome, "static"),
            xsrf_cookies = True,
            login_url = '/',
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

    def checkProfile (self, requestHandler, user):
        with self.conn as cur:
            cur.execute(*self.sql.check_user(user.userId, user.authenticator))
            try:
                p = Person(*cur.fetchone())
                log_gassman.debug('found profile: authId=%s, person=%s', user.userId, p)
            except TypeError:
                try:
                    # non ho trovato niente su db
                    cur.execute(*self.sql.create_contact(user.userId, 'I', user.authenticator))
                    contactId = cur.lastrowid
                    cur.execute(*self.sql.create_person(user.firstName, user.middleName, user.lastName))
                    p_id = cur.lastrowid
                    cur.execute(*self.sql.assign_contact(contactId, p_id))
                    if user.email:
                        cur.execute(*self.sql.create_contact(user.email, 'E', ''))
                        emailId = cur.lastrowid
                        cur.execute(*self.sql.assign_contact(emailId, p_id))
                    p = Person(p_id, user.firstName, user.middleName, user.lastName, None)
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

    def hasPermission (self, perm, personId):
        with self.conn as cur:
            cur.execute(*self.sql.has_permission(perm, personId))
            r = int(cur.fetchone()[0]) > 0
            log_gassman.debug('has permission: user=%s, perm=%s, r=%s', personId, perm, r)
            return r

class BaseHandler (tornado.web.RequestHandler):
    def get_current_user (self):
        c = self.get_secure_cookie('user', max_age_days=settings.COOKIE_MAX_AGE_DAYS)
        return int(c) if c else None

# faq, help e project per ora sono banali template statici
# ma in futuro potrebbero evolvere, quindi li imposto già così

class FaqHandler (BaseHandler):
    def get (self):
        self.render("faq.html")

class HelpHandler (BaseHandler):
    def get (self):
        self.render("help.html")

class ProjectHandler (BaseHandler):
    def get (self):
        self.render("project.html")

class IndexHandler (BaseHandler):
    def get (self):
        p = self.application.session(self).get_logged_user(None)
        if p is None:
            self.render('frontpage.html')
        elif p.account is None:
            self.redirect("/incomplete_profile.html")
        else:
            self.redirect("/home.html")

class IncompleteProfileHandler (tornado.web.RequestHandler):
    def get (self):
        s = self.application.session(self)
        p = s.get_logged_user(None)
        if not p or p.account is not None:
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
            if person.account:
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
        self.render('home.html')

class JsonBaseHandler (BaseHandler):
    def write_response (self, data):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        jsonlib.write_json(data, self)

    def write_error(self, status_code, **kwargs):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        etype, evalue, _ = kwargs.get('exc_info', ('', '', None))
        # tanto logga tornado
        #log_gassman.error('unexpected exception: %s/%s', etype, evalue)
        #log_gassman.debug('full stacktrace:\n', loglib.TracebackFormatter(tb))
        jsonlib.write_json([ str(etype), str(evalue) ], self)

class SelfAccountMovementsHandler (JsonBaseHandler):
    def post (self, fromIdx, toIdx):
        a = self.application.session(self).get_logged_user('not authenticated').account
        self.fetchMovements(a, fromIdx, toIdx)

    def fetchMovements (self, a, fromIdx, toIdx):
        with self.application.conn as cur:
            cur.execute(*self.application.sql.account_movements(a, int(fromIdx), int(toIdx)))
            data = list(cur)
        self.write_response(data)

class AccountMovementsHandler (SelfAccountMovementsHandler):
    def post (self, accId, fromIdx, toIdx):
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasPermission(sql.P_canCheckAccounts, u.id):
            raise Exception('permission denied')
        self.fetchMovements(accId, fromIdx, toIdx)

class AccountAmountHandler (JsonBaseHandler):
    def post (self):
        a = self.application.session(self).get_logged_user('not authenticated').account
        with self.application.conn as cur:
            cur.execute(*self.application.sql.account_amount(a))
            data = [ cur.fetchone()[0], '€' ]
        self.write_response(data)

class PermissionsHandler (JsonBaseHandler):
    '''Restituisce tutti i permessi visibili dall'utente loggato.
    '''
    def post (self):
        u = self.application.session(self).get_logged_user('not authenticated')
        with self.application.conn as cur:
            cur.execute(*self.application.sql.find_visible_permissions(u.id))
            data = list(cur)
        self.write_response(data)

class ProfileInfoHandler (JsonBaseHandler):
    def post (self):
        u = self.application.session(self).get_logged_user('not authenticated')
        with self.application.conn as cur:
            cur.execute(*self.application.sql.find_user_permissions(u.id))
            pp = [ p[0] for p in cur]
            cur.execute(*self.application.sql.find_user_csa(u.id))
            csa = list(cur)
            data = dict(
                    logged_user = u,
                    permissions = pp,
                    csa = csa
                    )
        self.write_response(data)

class AccountsIndexHandler (JsonBaseHandler):
    def post (self, fromIdx, toIdx):
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasPermission(sql.P_canCheckAccounts, u.id):
            raise Exception('permission denied')
        with self.application.conn as cur:
            cur.execute(*self.application.sql.accounts_index(int(fromIdx), int(toIdx)))
            data = list(cur)
        self.write_response(data)

class TransactionDetailHandler (JsonBaseHandler):
    def post (self, tid):
        # restituisco:
        # lines: [ id, desc, amount, accId ]
        # people: [ id, first, middle, last, accId ]
        # accounts: [ id, gc_name ]
        u = self.application.session(self).get_logged_user('not authenticated')
        with self.application.conn as cur:
            cur.execute(*self.application.sql.transaction_lines(tid))
            lines = list(cur)
            cur.execute(*self.application.sql.transaction_people(tid))
            people = dict([ (c[4], c) for c in cur])
            if not u.id in [c[0] for c in people.values()] and \
                not self.application.hasPermission(sql.P_canCheckAccounts, u.id):
                raise Exception('permission denied')
            cur.execute(*self.application.sql.transaction_account_gc_names(tid))
            accs = dict([ c for c in cur])
            data = dict(
                        lines = lines,
                        people = people,
                        accounts = accs,
                        )
        self.write_response(data)


class IncompleteProfilesHandler (JsonBaseHandler):
    '''
    Restituisce le persone senza account.
    '''
    def post (self):
        u = self.application.session(self).get_logged_user('not authenticated')
        if not self.application.hasPermission(sql.P_canAssignAccounts, u.id):
            raise Exception('permission denied')
        with self.application.conn as cur:
            cur.execute(*self.application.sql.find_users_without_account())
            pwa = list(cur)
            data = dict(
                        users_without_account=pwa
                        )
        self.write_response(data)


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
