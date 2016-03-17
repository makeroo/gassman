#!/usr/bin/env python3

import logging.config

import gassman_settings as settings

logging.config.dictConfig(settings.LOG)


log_gassman = logging.getLogger('gassman.notification_router')


def main():
    from gassman import ioc

    io_loop = ioc.io_loop()

    notification_router = ioc.notification_router()

    log_notification_router = logging.getLogger('gassman.notification_router')
    log_notification_router.info('Notification Router running...')

    io_loop.run_sync(notification_router)

    log_notification_router.info('Notification Router completed.')

if __name__ == '__main__':
    main()
