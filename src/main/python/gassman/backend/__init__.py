#!/usr/bin/env python3

"""
Created on 01/mar/2014

@author: makeroo
"""

import datetime
import hashlib
import logging
import sys
import json

import tornado.web

import gassman_settings as settings

import jsonlib
import loglib

import error_codes
from ..db import annotate_cursor_for_logging


log_gassman = logging.getLogger('gassman.backend')
log_gassman_db = logging.getLogger('gassman.application.db')


def rss_feed_id(pid):
    return hashlib.sha256((settings.COOKIE_SECRET + str(pid)).encode('utf-8')).hexdigest()


class GDataException (Exception):
    pass


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
        # self.account = p_current_account_id
        self.rssFeedId = p_rss_feed_id

    def __str__(self):
        return '%s (%s %s)' % (self.id, self.firstName, self.lastName)


class BaseHandler (tornado.web.RequestHandler):
    def get_current_user(self):
        c = self.get_secure_cookie('user', max_age_days=settings.COOKIE_MAX_AGE_DAYS)
        return int(c) if c else None

    def notify(self, template, receivers=None, reply_to=None, **namespace):
        subject = self.render_string(
            "%s.subject.email" % template,
            **namespace
        )
        body = self.render_string(
            "%s.body.email" % template,
            **namespace
        )
        self.application.notify_service.notify(
            subject.decode('UTF-8'),
            body.decode('UTF-8'),
            receivers,
            reply_to
        )

    def log_exception(self, typ, value, tb):
        if typ is GDataException and value.args[0] == error_codes.E_not_authenticated:
            log_gassman.warning("Not authenticated %s\n%r", self._request_summary(), self.request)


class HomeHandler (BaseHandler):
    def get(self):
        u = self.current_user
        if u is not None:
            with self.application.conn.connection() as cur:
                cur.execute(*self.application.conn.sql_factory.update_last_visit(u, datetime.datetime.utcnow()))
        self.xsrf_token  # leggere il cookie => generarlo
        self.render(
            'home.html',
            LOCALE=self.locale.code,
        )


class JsonBaseHandler (BaseHandler):
    notifyExceptions = False

    def post(self, *args):
        with self.application.conn.connection() as cur:
            annotate_cursor_for_logging(cur)
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
            self.application.notify_service.notify(
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


# lo lascio per futura pagina diagnostica: deve comunque ritornare sempre 0.0
# class CsaAmountHandler (JsonBaseHandler):
#    def do(self, cur, csa_id):
#        uid = self.current_user
#        if not self.application.has_permission_by_csa(cur, conn.sql_factory.P_canCheckAccounts, uid, csa_id):
#            raise GDataException(error_codes.E_permission_denied)
#        cur.execute(*self.application.conn.sql_factory.csa_amount(csa_id))
#        return cur.fetchone()


# TODO: riprisitnare quando si edita il profilo utente
# class PermissionsHandler (JsonBaseHandler):
#    '''Restituisce tutti i permessi visibili dall'utente loggato.
#    '''
#    def do(self, cur):
#        u = self.application.session(self).get_logged_user('not authenticated')
#        cur.execute(*self.application.conn.sql_factory.find_visible_permissions(u.id))
#        return list(cur)


# class ProfileInfoHandler (JsonBaseHandler):
#    def do(self, cur):
#        uid = self.current_user
#        if uid is None:
#            raise GDataException(error_codes.E_not_authenticated, 401)
#        cur.execute(*self.application.conn.sql_factory.find_user_permissions(uid))
#        pp = [ p[0] for p in cur ]
#        cur.execute(*self.application.conn.sql_factory.find_user_csa(uid))
#        csa = { id: { 'name': name, 'member': member } for id, name, member in cur.fetchall() }
#        cur.execute(*self.application.conn.sql_factory.find_user_accounts(uid))
#        accs = list(cur)
#        pq, cq, a = self.application.conn.sql_factory.people_profiles1([uid])
#        cur.execute(pq, a)
#        profile = self.application.conn.sql_factory.fetch_object(cur)
#        cur.execute(cq, a)
#        contacts = self.application.conn.sql_factory.iter_objects(cur)
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
