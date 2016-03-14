#!/usr/bin/env python3

"""
Created on 18/mar/2014

@author: makeroo
"""

import hashlib
import pymysql

import gassman_settings as settings

conn = pymysql.connect(host=settings.DB_HOST,
                       port=settings.DB_PORT,
                       user=settings.DB_USER,
                       passwd=settings.DB_PASSWORD,
                       db=settings.DB_NAME,
                       charset='utf8')


def rss_feed_id(person_id):
    return hashlib.sha256((settings.COOKIE_SECRET + str(person_id)).encode('utf-8')).hexdigest()

with conn as cur:
    cur.execute('SELECT id FROM person where rss_feed_id IS NULL')
    for pid in [l[0] for l in cur]:
        cur.execute('UPDATE person SET rss_feed_id=%s WHERE id=%s',
                    [
                     rss_feed_id(pid),
                     pid
                     ])
