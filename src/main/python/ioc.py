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
        io_loop
        )


def db_connection_arguments():
    return dict(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        passwd=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        charset='utf8'
    )


def sql_factory():
    import sql
    return sql
