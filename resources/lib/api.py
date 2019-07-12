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
        self.logged_in = True

    def play(self, media_id):
        # params = {
        #     'showEncodings': 'Android', #limits to 1080p
        #     'encodingsNew': 'true', #breaks playback
        # }

        data = self._session.get('/v1/media/{}'.format(media_id)).json()
        if 'error' in data:
            raise APIError(_(_.STREAM_ERRPR, msg=data['error']['message']))

        return data['data']['encodings'][0]['master_playlist_url']

    def categories(self):
        return self._session.get('/v1/categories').json()['data']

    def media(self, filter, term, collections=True, page=1):
        params = {
            'filterBy': filter,
            'term': term,
            'collections': collections,
            'limit': 20,
            'page': page,
        }

        return self._session.get('/v1/media', params=params).json()

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
        self.new_session()