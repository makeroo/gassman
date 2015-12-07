__author__ = 'makeroo'

import os
import logging

import tornado.ioloop
import tornado.web

logging.basicConfig(level=logging.DEBUG)

#https://accounts.google.com/o/oauth2/auth
# ?scope=profile+email&
# response_type=code&
# client_id=989424552810-e69up91er2e3ge8rjvvbqfsq93uclvfk.apps.googleusercontent.com&
# redirect_uri=http%3A%2F%2Flocalhost%3A8180%2Fauth%2Fgoogle
# &approval_prompt=auto

class OAuth2Server (tornado.web.Application):
    def __init__ (self):
        handlers = [
            #(r'^/$', IndexHandler),
            #(r'^/login.html$', LoginHandler),
            (r'^/o/oauth2/auth$', AuthHandler),
            ]
        codeHome = os.path.dirname(__file__)
        sett = dict(
            template_path = os.path.join(codeHome, 'oath2server_templates'),
            debug = True,
            )
        super().__init__(handlers, **sett)

class AuthHandler (tornado.web.RequestHandler):
    def get(self):
        u = self.get_query_argument('redirect_uri')
        self.render('login.html', redirect=u)

if __name__ == '__main__':
    io_loop = tornado.ioloop.IOLoop.instance()

    application = OAuth2Server()
    application.listen(9000)

    logging.info('OAuth2 server up and running...')

    io_loop.start()
