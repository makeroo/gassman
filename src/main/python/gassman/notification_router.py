

class NotificationRouter:
    def __init__(self, sql, mailer, conn_args):
        self.mailer = mailer
        self.conn_args = conn_args
        self.conn = None
        self.sql = sql

    def __call__(self):

        pass
