#!/usr/bin/env python3

"""
Created on 01/mar/2014

@author: makeroo
"""


def main():
    import logging.config

    import gassman_settings as settings

    logging.config.dictConfig(settings.LOG)

    import tornado.locale

    tornado.locale.load_translations(settings.TRANSLATIONS_PATH)

    from gassman import ioc

    application = ioc.gassman_backend()

    application.listen(settings.HTTP_PORT)

    log_gassman = logging.getLogger('gassman.backend')
    log_gassman.info('GASsMAN web server up and running...')

    ioc.io_loop().start()


if __name__ == '__main__':
    main()
