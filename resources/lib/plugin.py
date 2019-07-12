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
    folder.add_item(label=_.FEATURED, path=plugin.url_for(featured))
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

def _process_media(row):
    child_friendly = row.get('is_child_friendly', False) #TODO child friendly only settings?
    is_published   = row.get('is_published', True)
    is_collection  = row.get('is_collection', False)
    is_free        = row.get('is_free', False) 
    is_series      = row.get('is_numbered_series', False)
    
    if is_series:
        path = plugin.url_for(series, id=row['id'])
    elif is_collection:
        path = plugin.url_for(collection, id=row['id'])
    else:
        path = plugin.url_for(play, id=row['id'])

    return plugin.Item(
        label = row['title'],
        info  = {'plot': row['description'], 'duration': 120 if not is_free else row.get('duration', 0), 'year': row.get('year_produced')},
        art   = {'thumb': _image(row, 'image_medium')},
        path  = path,
        playable = not is_collection and not is_series,
    )

def _search_category(rows, id):
    for row in rows:
        if str(row['id']) == str(id):
            return row
        
        subcats = row.get('subcategories', [])
        if subcats:
            row = _search_category(subcats, id)
            if row:
                return row

    return None

@plugin.route()
def categories(id=None, **kwargs):
    folder = plugin.Folder(title=_.CATEGORIES)

    rows = api.categories()
    if id:
        row = _search_category(rows, id)
        if not row:
            raise PluginError(_(_.CATEGORY_NOT_FOUND, category_id=id))

        folder.title = row['label']
        rows = row.get('subcategories', [])

    for row in rows:
        subcategories = row.get('subcategories', [])

        if subcategories:
            path = plugin.url_for(categories, id=row['id'])
        else:
            path = plugin.url_for(medias, title=row['label'], filterby='category', term=row['name'])

        folder.add_item(
            label = row['label'],
            art   = {'thumb': _image(row, 'image_url')},
            path  = path,
        )

    return folder

@plugin.route()
def medias(title, filterby, term, collections=1, page=1, **kwargs):
    collections = int(collections)
    page = int(page)

    data = api.medias(filterby, term, collections=collections, page=page)
    total_pages = int(data['paginator']['total_pages'])

    folder = plugin.Folder(title=title)

    for row in data['data']:
        item = _process_media(row)
        folder.add_items([item])

    if total_pages > page:
        folder.add_item(
            label = _(_.NEXT_PAGE, next_page=page+1),
            path  = plugin.url_for(medias, title=title, filterby=filterby, term=term, page=page+1),
        )

    return folder

@plugin.route()
def collections(page=1, **kwargs):
    page = int(page)

    data = api.collections(page=page)
    total_pages = int(data['paginator']['total_pages'])

    folder = plugin.Folder(title=_.COLLECTIONS)

    for row in data['data']:
        folder.add_item(
            label = row['title'],
            info  = {'plot': row['description']},
            art   = {'thumb': _image(row, 'image_url')},
            path  = plugin.url_for(collection, id=row['id']),
        )

    if total_pages > page:
        folder.add_item(
            label = _(_.NEXT_PAGE, next_page=page+1),
            path  = plugin.url_for(collections, page=page+1),
        )

    return folder

@plugin.route()
def series(id, **kwargs):
    data   = api.series(id)
    folder = plugin.Folder(title=data['title'], fanart=_image(data, 'image_large'))

    for row in data.get('media', []):
        item = _process_media(row)
        folder.add_items([item])

    return folder

@plugin.route()
def collection(id, **kwargs):
    data   = api.collection(id)
    folder = plugin.Folder(title=data['title'], fanart=_image(data, 'background_url'))

    for row in data.get('media', []):
        item = _process_media(row)
        folder.add_items([item])

    return folder

@plugin.route()
def featured(**kwargs):
    folder = plugin.Folder(title=_.FEATURED)
    return folder

@plugin.route()
def search(query=None, page=1, **kwargs):
    page = int(page)

    if not query:
        query = gui.input(_.SEARCH, default=userdata.get('search', '')).strip()
        if not query:
            return
        userdata.set('search', query)

    data = api.medias('keyword', query, collections=True, page=page)
    total_pages = int(data['paginator']['total_pages'])

    folder = plugin.Folder(title=_(_.SEARCH_FOR, query=query, page=page, total_pages=total_pages))

    for row in data['data']:
        item = _process_media(row)
        folder.add_items([item])

    if total_pages > page:
        folder.add_item(
            label = _(_.NEXT_PAGE, next_page=page+1),
            path  = plugin.url_for(search, query=query, page=page+1),
        )

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
def play(id, **kwargs):
    data = api.media(id)
    item = _process_media(data)

    item.path = data['encodings'][0]['master_playlist_url']
    item.inputstream = inputstream.HLS()

    return item

@plugin.route()
def logout(**kwargs):
    if not gui.yes_no(_.LOGOUT_YES_NO):
        return

    api.logout()
    gui.refresh()