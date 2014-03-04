#!/usr/local/bin/python3
# encoding=utf-8

'''
Created on 01/mar/2014

@author: makeroo
'''

import logging.config
import tornado.httpserver
import tornado.web

import pymysql
import jsonlib

import sql

import gassman_settings as settings

logging.config.dictConfig(settings.LOG)

log_gassman = logging.getLogger('gassman.application')

ACCOUNT=4

class GassmanWebApp (tornado.web.Application):
    def __init__ (self, cur, sql):
        handlers = [
            (r'/account/movements', AccountMovementsHandler),
            (r'/account/amount', AccountAmountHandler),
            ]
        sett = dict(
            
            )
        super().__init__(handlers, **sett)
        self.cur = cur
        self.sql = sql
        

class AccountMovementsHandler (tornado.web.RequestHandler):
    def get (self):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'application/json')
        self.application.cur.execute(*self.application.sql.account_movements(ACCOUNT, 0, 5))
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
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(settings.HTTP_PORT)
    log_gassman.info('GASsMAN web server up and running...')
    io_loop.start()
