import posixpath

from tornado.template import BaseLoader, Template


class DbLoader(BaseLoader):
    """A template loader that loads from a db."""
    def __init__(self, conn, sql_factory, **kwargs):
        super(DbLoader, self).__init__(**kwargs)
        self.conn = conn
        self.sql_factory = sql_factory

    def resolve_path(self, name, parent_path=None):
        if parent_path and not parent_path.startswith("<") and \
            not parent_path.startswith("/") and \
                not name.startswith("/"):
            file_dir = posixpath.dirname(parent_path)
            name = posixpath.normpath(posixpath.join(file_dir, name))
        return name

    def _create_template(self, name):
        with self.conn.connection() as cur:
            q, a = self.sql_factory.template(name)
            cur.execute(q, a)
            try:
                template_text = cur.fetchone()[0]
            except TypeError:
                raise Exception('template not found', name)
            return Template(template_text, name=name, loader=self)
