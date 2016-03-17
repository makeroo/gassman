import datetime
import logging


log_notification_router = logging.getLogger('gassman.notification_router')


def datetime_floor(t, arrotondamento):
    """
    :param t: datetime instance
    :param arrotondamento: int
       0 identity
       1 zero microseconds (start of second)
       2 zero seconds (start of minute)
       3 zero minutes (start of our)
       4 zero hours (start of day)
       5 zero days (start of month)
       6 zero month (start of year)
    :return: rounded datetime instance
    """
    components = [
        t.year,
        t.month,
        t.day,
        t.hour,
        t.minute,
        t.second,
        t.microsecond
    ]
    components = components[:len(components) - arrotondamento] + [0] * arrotondamento
    return datetime.datetime(*components)


class DaylyTransactionReport:
    # gira da cron tutte le sere (eg. alle 23)
    pass


class WeeklyTransactionReport:
    # gira da cron tutte le settimane (eg. alle 23 di ogni sabato)
    pass


class NeverTransactionReport:
    # gira da cron tutte le sere (eg. alle 23)
    pass


class DeliveryDateReminder:
    class Generator:
        def __init__(self, frequency, advance, rounding, fetch_covered, fetch_uncovered):
            """
            :param frequency: (eg. 2 ore): giro alle 6am, 8am...
            :param advance: (eg. 6 ore): notifico dalle 12am alle 2pm...
            :param rounding: (eg. 1 ora): se giro alle 6:01, in realtà faccio finta di essere partito alle 6 esatte
            :param fetch_covered: considera i turni coperti
            :param fetch_uncovered: considera i turni scoperti
            """
            self.frequency = frequency
            self.advance = advance
            self.rounding = rounding
            self.fetch_covered = fetch_covered
            self.fetch_uncovered = fetch_uncovered

        def generate(self, router, cur):
            now = datetime.datetime.utcnow()
            t0 = datetime_floor(now, self.rounding)
            tstart = t0 + self.advance
            tend = tstart + self.frequency
            q, a = router.sql.delivery_dates_for_notifications(
                tstart,
                tend,
                self.fetch_covered,
                self.fetch_uncovered
            )
            cur.execute(q, a)
            return router.sql.iter_objects(cur)

    class Broadcaster:
        def __init__(self, notify_all):
            """
            :param notify_all: solo delivery_place o unknown / considera tutti
            :return:
            """
            self.notify_all = notify_all

        def broadcast(self, msg, router, cur):
            q, a = router.sql.people_index(
                msg['csa_id'],
                None,
                -1 if self.notify_all else msg['delivery_place_id'],
                None,
                False,
                -1,
                -1,
                None
            )
            cur.execute(q, a)
            return [(msg, row[0]) for row in cur.fetchall()]

    def __init__(self, generator, broadcaster, subject_if_covered, subject_if_uncovered, body_if_covered, body_if_uncovered):
        self.generator = generator
        self.broadcaster = broadcaster
        self.subject_if_covered = subject_if_covered
        self.subject_if_uncovered = subject_if_uncovered
        self.body_if_covered = body_if_covered
        self.body_if_uncovered = body_if_uncovered

    def __call__(self, router, cur):
        for event in self.generator.generate(router, cur):
            for msg, address in self.broadcaster.broadcast(event, router, cur):
                subject = router.template(
                    self.subject_if_covered if msg['shifts'] > 0 else
                    self.subject_if_uncovered,
                    msg
                )
                body = router.template(
                    self.body_if_covered if msg['shifts'] > 0 else
                    self.body_if_uncovered,
                    msg
                )
                router.send_email(
                    address,
                    subject,
                    body
                )


class NotificationRouter:
    def __init__(self, sql, mailer, conn_args, template_engine, config):
        self.mailer = mailer
        self.conn_args = conn_args
        self.conn = None
        self.sql = sql
        self.template_engine = template_engine
        self.config = config

    def __call__(self):
        for report in self.config:
            self._process_report(report)

    def _process_report(self, report):
        with self.conn as cur:
            report(self, cur)

    def template(self, templ_name, namespace):
        templ = self.template_engine.load(templ_name)
        return templ.generate(**namespace)

    def send_email(self, subject, body, dest, reply_to):
        s = subject.decode('UTF-8')
        b = body.decode('UTF-8')
        if self.mailer is None:
            log_notification_router.info('SMTP not configured, mail not sent: dest=%s, subj=%s\n%s', dest, subject, body)
        else:
            self.mailer.send(dest,
                             subject,
                             body,
                             reply_to
                             )
