from matthuisman.language import BaseLanguage

class Language(BaseLanguage):
    ASK_USERNAME         = 30001
    ASK_PASSWORD         = 30002
    LOGIN_ERROR          = 30003
    STREAM_ERRPR         = 30004
    CATEGORIES           = 30005
    COLLECTIONS          = 30006
    RECOMMENDED          = 30007
    WATCHLIST            = 30008
    WATCHING             = 30009
    HISTORY              = 30010

_ = Language()