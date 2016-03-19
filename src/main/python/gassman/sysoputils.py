import logging


log_gassman_notify = logging.getLogger('gassman.application.notify')


class NotifyService:
    def __init__(self, mailer, default_receiver):
        self.mailer = mailer
        self.default_receiver = default_receiver

    def notify(self, subject, body, receivers=None, reply_to=None):
        if self.mailer is None:
            log_gassman_notify.info('SMTP not configured, mail not sent: dest=%s, subj=%s\n%s', receivers, subject, body)
        else:
            self.mailer.send(receivers or self.default_receiver,
                             '[GASsMan] %s' % subject,
                             body,
                             reply_to
                             )
