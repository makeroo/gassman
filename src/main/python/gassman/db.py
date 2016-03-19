import sys
import logging
import pymysql

import tornado.ioloop

import loglib


log_gassman_db = logging.getLogger('gassman.application.db')


class Connection:
    def __init__(self, conn_args, db_check_interval, sql_factory, notify_service):
        self.conn_args = conn_args
        self.db_check_interval = db_check_interval
        self.conn = None
        self.sql_factory = sql_factory
        self.notify_service = notify_service

    def connection(self):
        if self.conn is None:
            self._connect()
        return self.conn

    def _connect(self):
        if self.conn is not None:
            try:
                self.conn.close()
                self.conn = None
            except:
                pass
        self.conn = pymysql.connect(**self.conn_args)
        tornado.ioloop.PeriodicCallback(self._check_conn, self.db_check_interval).start()

    def _check_conn(self):
        try:
            try:
                with self.conn as cur:
                    cur.execute(self.sql_factory.connection_check())
                    cur.fetchall()
            except pymysql.err.OperationalError as e:
                if e.args[0] == 2013:
                    # pymysql.err.OperationalError: (2013, 'Lost connection to MySQL server during query')
                    # provo a riconnettermi
                    log_gassman_db.warning('mysql closed connection, reconnecting')
                    self.connect()
                else:
                    raise
        except:
            etype, evalue, tb = sys.exc_info()
            log_gassman_db.fatal('db connection failed: cause=%s/%s', etype, evalue)
            # FIXME: notify!!
            self.notify_service.notify('[FATAL] No db connection', 'Connection error: %s/%s.\nTraceback:\n%s' %
                           (etype, evalue, loglib.TracebackFormatter(tb))
                           )
