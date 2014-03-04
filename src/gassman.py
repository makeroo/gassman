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

import gassman_settings as settings
import jsonlib
import sql


logging.config.dictConfig(settings.LOG)

log_gassman = logging.getLogger('gassman.application')

# TODO: autenticazione
# TODO: db asincrono

ACCOUNT=4 # FIXME: dedurlo dall'autenticazione

class GassmanWebApp (tornado.web.Application):
    def __init__ (self, cur, sql):
        handlers = [
            (r'/', IndexHandler),
            (r'/home.html', HomeHandler),
            (r'/account/movements/(\d+)/(\d+)', AccountMovementsHandler),
            (r'/account/amount', AccountAmountHandler),
            ]
        codeHome = os.path.dirname(__file__)
        sett = dict(
            cookie_secret = settings.COOKIE_SECRET,
            template_path = os.path.join(codeHome, 'templates'),
            static_path = os.path.join(codeHome, "static"),
            )
        super().__init__(handlers, **sett)
        self.cur = cur
        self.sql = sql

class IndexHandler (tornado.web.RequestHandler):
    def get (self):
        self.redirect('/home.html')

class HomeHandler (tornado.web.RequestHandler):
    def get (self):
        self.render('home.html')

class AccountMovementsHandler (tornado.web.RequestHandler):
    def get (self, fromIdx, toIdx):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        self.application.cur.execute(*self.application.sql.account_movements(ACCOUNT, int(fromIdx), int(toIdx)))
        data = list(self.application.cur)
        jsonlib.write_json(data, self)

class AccountAmountHandler (tornado.web.RequestHandler):
    def get (self):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        self.application.cur.execute(*self.application.sql.account_movements(ACCOUNT, 0, 5))
        data = self.application.cur.fetchone()
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
