import gassman_settings as settings


def io_loop():
    import tornado.ioloop

    return tornado.ioloop.IOLoop.instance()


def mailer():
    if settings.SMTP_SERVER is None:
        return None

    import asyncsmtp

    return asyncsmtp.Mailer(
        settings.SMTP_SERVER,
        settings.SMTP_PORT,
        settings.SMTP_NUM_THREADS,
        settings.SMTP_QUEUE_TIMEOUT,
        settings.SMTP_SENDER,
        io_loop
        )


def db_connection():
    from gassman.db import Connection
    return Connection(
        conn_args=dict(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            passwd=settings.DB_PASSWORD,
            db=settings.DB_NAME,
            charset='utf8'
        ),
        db_check_interval=settings.DB_CHECK_INTERVAL,
        sql_factory=sql_factory(),
        notify_service=notify_service(),
    )


def sql_factory():
    from . import sql
    return sql.SqlFactory()


def gassman_backend():
    from . import backend

    return backend.GassmanWebApp(
        db_connection(),
        notify_service()
    )


def notification_router(profile):
    from .notification_router import NotificationRouter

    return NotificationRouter(
        sql_factory(),
        mailer(),
        db_connection(),
        template_engine(),
        notification_router_configuration_manager(profile),
    )


def notification_router_configuration_manager(profile):
    from .notification_router import NotificationRouterConfigurationManager

    return NotificationRouterConfigurationManager(
        sql_factory(),
        db_connection(),
        profile,
    )


def template_engine():
    from tornado import template
    return template.Loader(
        settings.TEMPLATE_PATH,
        # autoescape=
        # template_whitespace=
    )


def notify_service():
    from .sysoputils import NotifyService
    return NotifyService(
        mailer(),
        settings.SMTP_RECEIVER
    )
