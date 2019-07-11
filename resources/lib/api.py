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

        self._session.headers.update({'Authorization': access_token)}
        self.logged_in = True

    def logout(self):
        userdata.delete('token')
        userdata.delete('deviceid')
        self.new_session()