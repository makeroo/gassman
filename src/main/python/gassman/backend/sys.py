from . import JsonBaseHandler

import gassman_version


class SysVersionHandler (JsonBaseHandler):
    def post(self):
        data = [gassman_version.version]
        self.write_response(data)
