import tornado.web
import tornado.auth
import tornado.gen
import tornado.httpclient
import tornado.escape

import oauth2lib


class GoogleUser (object):
    authenticator = 'Google2'

    def __init__(self, id_token):
        oauth2token = oauth2lib.extract_payload_from_oauth2_id_token(id_token['id_token'])
        self.userId = oauth2token['sub']
        self.email = oauth2token['email']
        self.access_token = id_token['access_token']

    @tornado.gen.coroutine
    def load_full_profile(self):
        http = tornado.httpclient.AsyncHTTPClient()
        response = yield http.fetch(
            'https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token=' + self.access_token,
            method="GET"
        )
        if response.error:
            raise Exception('Google auth error: %s' % str(response))

        profile = tornado.escape.json_decode(response.body)
        self.firstName = profile.get('given_name')
        self.middleName =  None
        self.lastName = profile.get('family_name')
        self.gProfile = profile.get('link')
        self.picture = profile.get('picture')
        # altri attributi: id, email, gender, locale


class GoogleAuthLoginHandler (tornado.web.RequestHandler, tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            id_token = yield self.get_authenticated_user(
                redirect_uri=self.settings['google_oauth_redirect'],
                code=self.get_argument('code')
                )
            token_user = GoogleUser(id_token)
            # check_profile ritorna person ma a me interessa solo la registrazione su db
            yield self.application.check_profile(self, token_user)
            self.redirect("/home.html")
        else:
            yield self.authorize_redirect(
                redirect_uri=self.settings['google_oauth_redirect'],
                client_id=self.settings['google_oauth']['key'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})


# TODO: facebook login


# TODO: twitter login
