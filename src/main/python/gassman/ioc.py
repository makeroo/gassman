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
    )


def sql_factory():
    from . import sql
    return sql.SqlFactory()


def gassman_backend():
    from . import backend

    return backend.GassmanWebApp(
        sql_factory(),
        mailer(),
        db_connection(),
    )


def notification_router():
    from . import notification_router

    return notification_router.NotificationRouter(
        sql_factory(),
        mailer(),
        db_connection(),
        template_engine(),
        # TODO: config!
    )


def template_engine():
    from tornado import template
    return template.Loader(
        settings.TEMPLATE_PATH,
        # autoescape=
        # template_whitespace=
    )
