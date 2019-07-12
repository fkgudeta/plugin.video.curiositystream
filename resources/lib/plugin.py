from matthuisman import plugin, gui, userdata, signals, inputstream
from matthuisman.log import log
from matthuisman.exceptions import PluginError

from .api import API
from .language import _

api = API()

@signals.on(signals.BEFORE_DISPATCH)
def before_dispatch():
    api.new_session()
    plugin.logged_in = api.logged_in

@plugin.route('')
def index(**kwargs):
    folder = plugin.Folder()

    folder.add_item(label=_.CATEGORIES, path=plugin.url_for(categories))
    folder.add_item(label=_.COLLECTIONS, path=plugin.url_for(collections))
    folder.add_item(label=_.RECOMMENDED, path=plugin.url_for(recommended))
    folder.add_item(label=_.SEARCH, path=plugin.url_for(search))

    if not api.logged_in:
        folder.add_item(label=_(_.LOGIN, _bold=True), path=plugin.url_for(login), _position=0)
    else:
        folder.add_item(label=_.WATCHLIST, path=plugin.url_for(watchlist))
        folder.add_item(label=_.WATCHING, path=plugin.url_for(watching))
        folder.add_item(label=_.HISTORY, path=plugin.url_for(history))
        folder.add_item(label=_.LOGOUT, path=plugin.url_for(logout))

    folder.add_item(label=_.SETTINGS, path=plugin.url_for(plugin.ROUTE_SETTINGS))

    return folder

def _image(row, key):
    if key in row and not row[key].lower().strip().endswith('missing.png'):
        return row[key]

    return None

def _process_categories(rows):
    items = []

    for row in rows:
        subcategories = row.get('subcategories', [])

        if subcategories:
            path = plugin.url_for(categories, id=row['id'])
        else:
            path = plugin.url_for(media, title=row['label'], filterby='category', term=row['name'])

        item = plugin.Item(
            label = row['label'],
            art   = {'thumb': _image(row, 'image_url'), 'fanart': _image(row, 'background_url')},
            path  = path,
        )

        items.append(item)

    return items

def _get_category(rows, id):
    def _search(rows):
        for row in rows:
            if str(row['id']) == str(id):
                return row
            else:
                row = _search(row.get('subcategories', []))
                if row:
                    return row

        return None

    return _search(rows)

def _process_media(rows):
    items = []

    for row in rows:
        item = plugin.Item(
            label = row['title'],
            info  = {'plot': row['description'], 'duration': row['duration']},
            art   = {'thumb': _image(row, 'image_medium')},
            path  = plugin.url_for(play, media_id=row['id']),
            playable = True,
        )

        items.append(item)

    return items

@plugin.route()
def categories(id=None, **kwargs):
    folder = plugin.Folder(title=_.CATEGORIES)

    rows = api.categories()
    if id:
        row = _get_category(rows, id)
        if not row:
            raise #TODO language error

        folder.title = row['label']
        rows = row.get('subcategories', [])

    items = _process_categories(rows)
    folder.add_items(items)

    return folder

@plugin.route()
def media(title, filterby, term, page=1, **kwargs):
    page = int(page)

    folder = plugin.Folder(title=title)

    data = api.media(filterby, term, page=page)
    items = _process_media(data['data'])
    folder.add_items(items)

    if int(data['paginator']['total_pages']) > page:
        folder.add_item(
            label = 'Next Page', #TODO language me!
            path  = plugin.url_for(media, title=title, filterby=filterby, term=term, page=page+1)
        )

    return folder

@plugin.route()
def collections(**kwargs):
    folder = plugin.Folder(title=_.COLLECTIONS)
    return folder

@plugin.route()
def recommended(**kwargs):
    folder = plugin.Folder(title=_.RECOMMENDED)
    return folder

@plugin.route()
def search(**kwargs):
    folder = plugin.Folder(title=_.SEARCH)
    return folder

@plugin.route()
def watchlist(**kwargs):
    folder = plugin.Folder(title=_.WATCHLIST)
    return folder

@plugin.route()
def watching(**kwargs):
    folder = plugin.Folder(title=_.WATCHING)
    return folder

@plugin.route()
def history(**kwargs):
    folder = plugin.Folder(title=_.HISTORY)
    return folder

@plugin.route()
def login(**kwargs):
    username = gui.input(_.ASK_USERNAME, default=userdata.get('username', '')).strip()
    if not username:
        return

    userdata.set('username', username)

    password = gui.input(_.ASK_PASSWORD, hide_input=True).strip()
    if not password:
        return

    api.login(username=username, password=password)
    gui.refresh()

@plugin.route()
def play(media_id, **kwargs):
    url = api.play(media_id)

    return plugin.Item(
        path = url,
        inputstream = inputstream.HLS(),
    )

@plugin.route()
@plugin.login_required()
def logout(**kwargs):
    if not gui.yes_no(_.LOGOUT_YES_NO):
        return

    api.logout()
    gui.refresh()\