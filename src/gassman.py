#!/usr/local/bin/python3
# encoding=utf-8

'''
Created on 01/mar/2014

@author: makeroo
'''

import logging.config
import os.path

import pymysql
import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.gen
#import tornado.escape

import gassman_settings as settings
import jsonlib
import sql

logging.config.dictConfig(settings.LOG)

log_gassman = logging.getLogger('gassman.application')

# TODO: db asincrono

class GoogleUser (object):
    authenticator = 'Google'

    def __init__ (self, userInfo):
        self.userId = userInfo['claimed_id']
        self.firstName = userInfo['first_name']
        self.middleName = None
        self.lastName = userInfo['last_name']
        self.email = userInfo['email']

class Session (object):
    def __init__ (self, app):
        self.application = app
        self.logged_user = None

    def get_logged_user (self, error='not authenticated'):
        if not self.logged_user:
            if error:
                raise Exception(error)
            else:
                return None
        return self.logged_user

class Person (object):
    def __init__ (self, p_id, p_first_name, p_middle_name, p_last_name, p_current_account_id):
        self.id = p_id
        self.firstName = p_first_name
        self.middleName = p_middle_name
        self.lastName = p_last_name
        self.account = p_current_account_id

class GassmanWebApp (tornado.web.Application):
    def __init__ (self, cur, sql):
        handlers = [
            (r'^/$', IndexHandler),
            (r'^/home.html$', HomeHandler),
            (r'^/auth/google$', GoogleAuthLoginHandler),
            (r'^/incomplete_profile.html$', IncompleteProfileHandler),
            (r'^/account/movements/(\d+)/(\d+)$', AccountMovementsHandler),
            (r'^/account/amount$', AccountAmountHandler),
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
        self.cur = cur
        self.sql = sql
        self.sessions = dict()

    def checkProfile (self, requestHandler, user):
        self.cur.execute(*self.sql.check_user(user.userId, user.authenticator))
        try:
            p = Person(*self.cur.fetchone())
        except TypeError:
            # non ho trovato niente su db
            self.cur.execute(*self.sql.create_contact(user.userId, 'I', user.authenticator))
            contactId = self.cur.lastrowid
            self.cur.execute(*self.sql.create_person(user.firstName, user.middleName, user.lastName))
            p_id = self.cur.lastrowid
            self.cur.execute(*self.sql.assign_contact(contactId, p_id))
            if user.email:
                self.cur.execute(*self.sql.create_contact(user.email, 'E', ''))
                emailId = self.cur.lastrowid
                self.cur.execute(*self.sql.assign_contact(emailId, p_id))
            p = Person(p_id, user.firstName, user.middleName, user.lastName, None)
        requestHandler.set_secure_cookie("user", tornado.escape.json_encode(p.id))
        return p
        # TODO: transazioni

    def session (self, requestHandler):
        xt = requestHandler.xsrf_token
        s = self.sessions.get(xt, None)
        if s is None:
            s = Session(self)
            self.sessions[xt] = s
            pid = requestHandler.current_user
            if pid:
                self.cur.execute(*self.sql.find_person(pid))
                pdata = self.cur.fetchone()
                if pdata:
                    s.logged_user = Person(*pdata)
                    log_gassman.info('created session: token=%s, user=%s', xt, s.logged_user)
                else:
                    log_gassman.warning('created session, user not found: token=%s, pid=%s', xt, pid)
            else:
                log_gassman.info('created session: token=%s', xt)
        return s


class BaseHandler (tornado.web.RequestHandler):
    def get_current_user (self):
        c = self.get_secure_cookie('user', max_age_days=settings.COOKIE_MAX_AGE_DAYS)
        return int(c) if c else None

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

class AccountMovementsHandler (BaseHandler):
    def post (self, fromIdx, toIdx):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        a = self.application.session(self).logged_user.account
        self.application.cur.execute(*self.application.sql.account_movements(a, int(fromIdx), int(toIdx)))
        data = list(self.application.cur)
        jsonlib.write_json(data, self)

    def write_error(self, status_code, **kwargs):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        etype, evalue, _ = kwargs.get('exc_info', ('', '', None))
        # tanto logga tornado
        #log_gassman.error('unexpected exception: %s/%s', etype, evalue)
        #log_gassman.debug('full stacktrace:\n', loglib.TracebackFormatter(tb))
        jsonlib.write_json([ str(etype), str(evalue) ], self)

class AccountAmountHandler (BaseHandler):
    def post (self):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        a = self.application.session(self).logged_user.account
        self.application.cur.execute(*self.application.sql.account_amount(a))
        data = [ self.application.cur.fetchone()[0], '€' ]
        jsonlib.write_json(data, self)

if __name__ == '__main__':
    io_loop = tornado.ioloop.IOLoop.instance()
    conn = pymysql.connect(host=settings.DB_HOST,
                           port=settings.DB_PORT,
                           user=settings.DB_USER,
                           passwd=settings.DB_PASSWORD,
                           db=settings.DB_NAME,
                           charset='utf8')
    application = GassmanWebApp(conn.cursor(), sql)
    application.listen(settings.HTTP_PORT)
    log_gassman.info('GASsMAN web server up and running...')
    io_loop.start()
