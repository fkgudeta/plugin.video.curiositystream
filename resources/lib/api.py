import hashlib

from matthuisman import userdata, settings
from matthuisman.session import Session
from matthuisman.exceptions import Error
from matthuisman.log import log

from .constants import HEADERS, API_URL
from .language import _

class APIError(Error):
    pass

class API(object):
    def new_session(self):
        self.logged_in = False
        self._session  = Session(HEADERS, base_url=API_URL)
        self._set_authentication()
        
    def _set_authentication(self):
        access_token = userdata.get('token')
        if not access_token:
            return

        self._session.headers.update({'X-Auth-Token': access_token})
        #self._session.headers.update({'x-session-token': session_token})
        self.logged_in = True

    # def _eustatus(self):
        # r = self._session.get('.')
        # r.headers.get("x-eu-user");
        # r.headers.get("x-session-token");

    def play(self, media_id):
        params = {
           # 'showEncodings': 'Android',
            #'encodingsNew': 'true', #breaks playback
        }

        data = self._session.get('/v1/media/{}'.format(media_id), params=params).json()

        return data['data']['encodings'][0]['master_playlist_url']

    def login(self, username, password):
        self.logout()

        payload = {
            'email': username,
            'password': password,
            'platform': 'google',
        }

        data = self._session.post('/v1/login/', data=payload).json()
        if 'error' in data:
            try:
                msg = data['error']['message']['base'][0]
            except:
                msg = ''

            raise APIError(_(_.LOGIN_ERROR, msg=msg))
        
        userdata.set('token', data['message']['auth_token'])
        self._set_authentication()

    def logout(self):
        userdata.delete('token')
      #  userdata.delete('deviceid')
        self.new_session()