import hashlib

from matthuisman import userdata, settings
from matthuisman.session import Session
from matthuisman.exceptions import Error
from matthuisman.log import log
from matthuisman import mem_cache

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

    @mem_cache.cached()
    def categories(self):
        return self._session.get('/v1/categories').json()['data']

    @mem_cache.cached()
    def series(self, id):
        return self._session.get('/v2/series/{}'.format(id)).json()['data']

    @mem_cache.cached()
    def featured(self):
        return self._session.get('/v2/featured').json()

    @mem_cache.cached()
    def sections(self, id, page=1):
        params = {
            'cache': False,
            'collections': True,
            'media_limit': 36,
            'page': page,
        }

        return self._session.get('/v1/sections/{}/mobile'.format(id)).json()['data']['groups']

    @mem_cache.cached()
    def collection(self, id, flattened=False):
        params = {
            'flattened': flattened,
        }

        return self._session.get('/v2/collections/{}'.format(id), params=params).json()['data']

    @mem_cache.cached()
    def collections(self, flattened=False, excludeMedia=True, page=1):
        params = {
            'flattened': flattened,
            'excludeMedia': excludeMedia,
            'limit': 20,
            'page': page,
        }

        return self._session.get('/v2/collections', params=params).json()

    def filter_media(self, filterby, term, collections=True, page=1):
        params = {
            'filterBy': filterby,
            'term': term,
            'collections': collections,
            'limit': 20,
            'page': page,
        }

        return self._session.get('/v1/media', params=params).json()

    def media(self, id):
        # params = {
        #    'showEncodings': 'Android', #limits to 1080p
        #    'encodingsNew': 'true', #breaks playback
        # }

        return self._session.get('/v1/media/{}'.format(id)).json()['data']

    def logout(self):
        userdata.delete('token')
        mem_cache.empty()
        self.new_session()