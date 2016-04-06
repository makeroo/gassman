#!/usr/bin/env python3


def main():
    import sys
    import os.path
    import argparse
    import logging.config

    import gassman_settings as settings

    logging.config.dictConfig(settings.LOG)

    from gassman.db import annotate_cursor_for_logging
    from gassman import ioc

    logger = logging.getLogger('gassman.notification_template_loader')

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--template-dir", help="path to templates directory")
    cmd_line = parser.parse_args()

    if cmd_line.template_dir is None:
        logger.error('missing template dir')
        sys.exit(1)

    if not os.path.isdir(cmd_line.template_dir):
        logger.error('template dir is not a directory')
        sys.exit(1)

    db = ioc.db_connection()

    for f in os.listdir(cmd_line.template_dir):
        fp = os.path.join(cmd_line.template_dir, f)
        if not os.path.isfile(fp):
            logger.debug('skipping %s', f)
        with open(fp, 'rb') as fh:
            tpl = fh.read()
        with db.connection() as cur:
            annotate_cursor_for_logging(cur)

            q, a = db.sql_factory.template_update(f, tpl)
            cur.execute(q, a)

            if cur.rowcount == 0:
                q, a = db.sql_factory.template_insert(f, tpl)
                cur.execute(q, a)
                logger.info('new template %s', f)
            else:
                logger.info('updated template %s', f)

    sys.exit(0)


if __name__ == '__main__':
    main()
