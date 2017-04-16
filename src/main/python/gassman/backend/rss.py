import tornado.web


from ..templateutils import currency, pubDate, shortDate


class RssFeedHandler (tornado.web.RequestHandler):
    def get(self, rss_id):
        self.clear_header('Content-Type')
        self.add_header('Content-Type', 'text/xml')
        with self.application.conn.connection() as cur:
            cur.execute(*self.application.conn.sql_factory.rss_user(rss_id))
            p = cur.fetchone()
            cur.execute(*self.application.conn.sql_factory.rss_feed(rss_id))
            self.render('rss.xml',
                        person=p,
                        items=cur,
                        shortDate=shortDate,
                        pubDate=pubDate,
                        currency=currency,
                        )
