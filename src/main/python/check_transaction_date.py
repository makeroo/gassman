#!/usr/bin/env python

import datetime
import logging
import argparse


NO_DATE = object()
TO_OFFSET = datetime.timedelta(days=365 * 100)
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def sql_date_literal(d):
    return "'%s'" % d.strftime(DATE_FORMAT)


class Transaction:
    def __init__(self, tid, tdate, modified_by, cc_type, logdate):
        self.id = tid
        self.tdate = tdate
        self.modified_by = modified_by
        self.cc_type = cc_type
        self.logdate = logdate
        self.lines = []
        self.adjusted_tdate = None

    def __str__(self):
        return '%s-%s(%s%s)' % (self.cc_type, self.id, self.tdate, ' MOD' if self.modified_by else '')


class TransactionLine:
    def __init__(self, lid, acc_id):
        self.id = lid
        self.acc_id = acc_id


class AccountWithoutOwnership (Exception):
    pass


class Account:
    def __init__(self, aid, gc_name, gc_type):
        self.id = aid
        self.gc_name = gc_name
        self.gc_type = gc_type
        self.ownerships = {}  # da owner_id in [AccountPerson]
        self.need_ownership = False

    def __str__(self):
        return '%s-%s(%s)' % (self.gc_type, self.id, self.gc_type)

    def select_invalid_ownership_by_date(self, d):
        """
        A me interessa che per ogni transazione X su un conto A
        esista almeno una ownership O il cui intervallo contenga X.
        Qualora non esista, non è banale individuare quella O da estendere
        per risolvere la situazione.
        :param d: Data della transazione
        :return: Ownership da correggere se necessario, o None.
        """

        ownership_to_correct = None

        def take_nearest(ownership):
            return ownership if ownership.distance(d) < ownership_to_correct.distance(d) else ownership_to_correct

        for owner_id, ownerships in self.ownerships.items():
            def select_invalid_ownership_by_date():
                for o in ownerships:
                    if d < o.from_date:
                        return o
                    if o.to_date is None or d <= o.to_date:
                        o.transactions += 1
                        return None
                # se sono qua significa che nessuna ownership contiene la transazione
                # e che tutte le sono precedenti: prendo quindi l'ultima, sicuramente la più vicina
                return ownerships[-1]

            selected_ownership = select_invalid_ownership_by_date()

            if selected_ownership is None:
                return None
            if ownership_to_correct is None:
                ownership_to_correct = selected_ownership
            else:
                ownership_to_correct = take_nearest(selected_ownership)

        if ownership_to_correct is None:
            raise AccountWithoutOwnership(self.id)

        return ownership_to_correct


class AccountPerson:
    def __init__(self, apid, acc_id, from_date, to_date, owner_id):
        self.id = apid
        self.acc_id = acc_id
        self.original_from = from_date
        self.original_to = to_date
        self.owner_id = owner_id

        self.from_date = self.original_from
        self.to_date = self.original_to

        self.transactions = 0

    def __str__(self):
        return 'acc:%s-own:%s(%s-%s)' % (self.acc_id, self.owner_id, self.from_date,
                                         self.to_date if self.to_date is not None else '')

    __repr__ = __str__

    def distance(self, date):
        if date < self.from_date:
            return self.from_date - date
        elif self.to_date is not None and self.to_date < date:
            return (date - self.to_date) + TO_OFFSET
        return 0

    def adjusted_date(self, td):
        if td < self.from_date:
            self.from_date = td
        else:
            if self.to_date is None:
                raise Exception('trying to close ownership: id=%s', self.id)
            if self.to_date > td:
                raise Exception('trying to shrinkownership: id=%s', self.id)
            self.to_date = td


class CheckTransactionDate:
    def __init__(self, db, logger):
        self.db = db
        self.logger = logger
        self.transactions = {}
        self.accounts = {}

    def collect(self):
        with self.db.connection() as cur:
            cur.execute('SELECT t.id, t.transaction_date, t.modified_by_id, t.cc_type, tl.log_date FROM transaction t JOIN transaction_log tl  ON tl.transaction_id=t.id')
            for tid, tdate, modified_by, cc_type, logdate in cur.fetchall():
                if tdate is None:
                    self.logger.error('transaction without date: id=%s', tid)
                if logdate is None:
                    self.logger.error('transaction without log: id=%s', tid)
                t = Transaction(tid, tdate, modified_by, cc_type, logdate)
                if tid in self.transactions:
                    self.logger.error('transaction has multiple logs: id=%s', tid)
                self.transactions[t.id] = t
            self.logger.debug('found %s transactions', len(self.transactions))

            cur.execute('SELECT l.id, l.account_id, l.transaction_id FROM transaction_line l')
            for row in cur.fetchall():
                l = TransactionLine(row[0], row[1])
                self.transactions[row[2]].lines.append(l)
            cur.execute('SELECT a.id, a.gc_name, a.gc_type FROM account a')
            for row in cur.fetchall():
                a = Account(*row)
                self.accounts[a.id] = a
            self.logger.debug('found %s accounts', len(self.accounts))

            cur.execute('SELECT ap.id, ap.account_id, ap.from_date, ap.to_date, ap.person_id FROM account_person ap ORDER BY ap.account_id, ap.from_date')
            for apid, acc_id, from_date, to_date, own_id in cur.fetchall():
                ap = AccountPerson(apid, acc_id, from_date, to_date, own_id)
                if from_date is None:
                    self.logger.error('account_person with NULL from_date: id=%s', apid)
                    ap.from_date = to_date - datetime.timedelta(days=1) if to_date is not None \
                        else datetime.datetime.utcnow()
                elif ap.to_date is not None and ap.to_date < from_date:
                    self.logger.error('illegal ownership interval: id=%s', apid)
                    ap.to_date = ap.from_date
                self.accounts[ap.acc_id].ownerships.setdefault(ap.owner_id, []).append(ap)

            for a in self.accounts.values():
                for owner_id, ownerships in a.ownerships.items():
                    ownerships.sort(key=lambda o: o.from_date)
                    for idx, o in zip(range(len(ownerships) - 1), ownerships):
                        next_o = ownerships[idx + 1]
                        if o.to_date is None:
                            self.logger.error('two non closed ownerships: %s-%s', o.id, next_o.id)
                            o.to_date = next_o.from_date  # - datetime.timedelta(seconds=1)
                        elif o.to_date > next_o.from_date:
                            self.logger.error('overlapping ownerships: %s-%s', o.id, next_o.id)
                            o.to_date = next_o.from_date


    def analyze(self):
        for t in self.transactions.values():
            td = t.tdate
            if td is None:
                if t.logdate is None:
                    td.adjusted_tdate = NO_DATE
                    continue
                else:
                    td = t.logdate
                    t.adjusted_tdate = td
            for l in t.lines:
                a = self.accounts[l.acc_id]
                try:
                    selected_ownership = a.select_invalid_ownership_by_date(td)
                    if selected_ownership is None:
                        continue
                    if t.modified_by:
                        self.logger.debug('modified transaction: ownership-to-modify=%s, transaction=%s',
                                          selected_ownership, t)
                    else:
                        selected_ownership.adjusted_date(td)
                        self.logger.info('ownership to modify: ownership=%s, transaction=%s', selected_ownership, t)
                except AccountWithoutOwnership:
                    level = logging.DEBUG if a.gc_type in ('KITTY', ) or (
                        t.cc_type in ('g', 'w', 'q') and a.gc_type in ('EXPENSE', )
                    ) or (
                        t.cc_type in ('g', 'd') and a.gc_type in ('INCOME', )
                    ) or (
                        t.cc_type in ('g', ) and a.gc_type in ('EQUITY', 'EXPENSE-old', 'BANK')
                    ) else logging.ERROR
                    self.logger.log(level, 'account without ownership: id=%s, transaction=%s', a, t)
                    if level == logging.ERROR:
                        a.need_ownership = True

    def sql_report(self, fix_db=False):
        with self.db.connection() as cur:
            for t in self.transactions.values():
                if t.adjusted_tdate is None:
                    continue
                elif t.adjusted_tdate is NO_DATE:
                    print("-- can't fix transaction %s, no logdate", t.id)
                else:
                    q, a = "UPDATE transaction SET transaction_date=%s WHERE id=%s", [t.adjusted_tdate, t.id]
                    print(q % (sql_date_literal(a[0]), a[1]) + ';')
                    if fix_db:
                        cur.execute(q, a)
            for a in self.accounts.values():
                if a.need_ownership:
                    print("-- can't fix account without ownership %s", a.id)
                for owner_id, ownerships in a.ownerships.items():
                    for o in ownerships:
                        if o.from_date is not None and o.from_date is o.to_date and o.transactions == 0:
                            q, a = "DELETE FROM account_person WHERE id=%s", [o.id]
                            print(q % a[0] + ';')
                            if fix_db:
                                cur.execute(q, a)
                        else:
                            if o.from_date is not o.original_from:
                                q, a = "UPDATE account_person SET from_date=%s WHERE id=%s", [o.from_date, o.id]
                                print(q % (sql_date_literal(a[0]), a[1]) + ';')
                                if fix_db:
                                    cur.execute(q, a)
                            if o.to_date is not o.original_to:
                                q, a = "UPDATE account_person SET to_date=%s WHERE id=%s", [o.to_date, o.id]
                                print(q % (sql_date_literal(a[0]), a[1]) + ';')
                                if fix_db:
                                    cur.execute(q, a)


def main():
    parser = argparse.ArgumentParser(
        description='Transaction date consistency validator'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='increment verbosity',
    )

    parser.add_argument(
        '--fix',
        type=bool,
        help='fix dates',
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR - 10 * args.verbose)

    from gassman import ioc

    db = ioc.db_connection()

    app = CheckTransactionDate(db, logging)
    app.collect()
    app.analyze()
    app.sql_report(args.fix)


if __name__ == '__main__':
    main()
