#!/usr/bin/env python3

"""
Created on 01/mar/2014

@author: makeroo
"""

import logging.config

import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.gen
import tornado.httpclient
import tornado.escape

import gassman_settings as settings


logging.config.dictConfig(settings.LOG)


def main():
    import ioc

    tornado.locale.load_translations(settings.TRANSLATIONS_PATH)

    application = ioc.gassman_backend()

    application.listen(settings.HTTP_PORT)

    log_gassman = logging.getLogger('gassman.backend')
    log_gassman.info('GASsMAN web server up and running...')

    ioc.io_loop().start()

if __name__ == '__main__':
    main()
