#!/usr/bin/python
# -*- coding: utf-8 -*-

import operator
import urllib, urllib2, urlparse
import sys
import math
import xbmc, xbmcaddon, xbmcplugin, xbmcgui
import cookie_store
import api
import re
import const
import utils

__addon__ = xbmcaddon.Addon(id=const.ADDON_ID)
__settings__ = xbmcaddon.Addon(id=const.ADDON_ID)
__icon__ = __addon__.getAddonInfo('icon')
__skinsdir__ = "DefaultSkin"
__language__ = __addon__.getLocalizedString

DEFAULT_QUALITY = __settings__.getSetting("video_quality")
DEFAULT_STREAM_TYPE = __settings__.getSetting("stream_type")

_ADDON_PATH = xbmc.translatePath(__addon__.getAddonInfo('path'))
if (sys.platform == 'win32') or (sys.platform == 'win64'):
    _ADDON_PATH = _ADDON_PATH.decode('utf-8')
handle = int(sys.argv[1])


def log(str):
    xbmc.log("%s FLX_LOG MAIN: %s" % (const.PLUGIN_ID, str))


import auth_window as auth
import free_limit_window as free_limit

Auth = auth.Auth(__settings__)


# Show pagination
def show_pagination(resp_data, action, qp):
    # Add "next page" button
    if 'total' in resp_data and resp_data['total'] and 'page' in resp_data:
        cur_page = int(resp_data['page'])
        total_items = int(resp_data['total'])
        items_per_page = int(resp_data['items_per_page'])
        total_pages = math.ceil(total_items / items_per_page)
        log("cur_page: %s / total_pages: %s" % (cur_page, total_pages))
        if cur_page + 1 <= total_pages:
            qp['p'] = cur_page + 1
            li = xbmcgui.ListItem("[COLOR FFFFF000]Next page [%s][/COLOR]" % qp['p'])
            link = get_internal_link(action, qp)
            xbmcplugin.addDirectoryItem(handle, link, li, True)
        if cur_page > 1:
            qp['p'] = cur_page - 1
            li = xbmcgui.ListItem("[COLOR FFFFF000]Previous page [%s][/COLOR]" % qp['p'])
            link = get_internal_link(action, qp)
            xbmcplugin.addDirectoryItem(handle, link, li, True)


def get_page(qp):
    if 'p' in qp:
        return qp['p']
    else:
        return 1


def show_lists(items):
    log("show_lists items.length = %s" % (items and str(len(items))))
    supported_acts = ['items', 'list', 'search', 'favorites', 'collections', 'profiles']
    for index, item in enumerate(items):
        if 'act' in item:
            act = item['act']
            if act not in supported_acts:
                continue

            if act == 'profiles' and not cookie_store.has_multiple_profiles(__settings__):
                continue

            if act == 'favorites':
                act = 'items'

            title = item['title'].encode('utf-8')
            if 'color' in item:
                title = "[COLOR %s]%s[/COLOR]" % (item['color'], title)
            li = xbmcgui.ListItem(title)
            link = get_internal_link(act, item)
            xbmcplugin.addDirectoryItem(handle, link, li, True)


# Fill directory for items
def show_items(items, options={}):
    log("show_items: Total items: %s, options: %s" % (str(len(items)), options))

    if 'act' in options and options['act'] == 'favorites':
        # items = sorted(items, key = lambda x: (x['type'], x['title']), reverse=True)
        items = sorted(items, key=lambda x: (x['title']))
        items = sorted(items, key=lambda x: (x['type']), reverse=True)

    xbmcplugin.setContent(handle, 'movies')
    # Fill list with items
    for index, item in enumerate(items):
        isdir = False

        action = 'play'
        qp = {'id': item['id']}
        title = ''
        item_type = item.get('type')
        if item.get('title'):
            title = item['title'].encode('utf-8')

        info = None

        if item_type == 'tvshow':
            action = 'tvshow'
            qp['url'] = item['url']
            info = utils.video_info(item, {'mediatype': 'tvshow'})
            isdir = True
            if options.get('show_tvshow_at_title'):
                title = '[COLOR FFFFF000]TV Show:[/COLOR] ' + title
        if item_type == 'tvseason':
            action = 'tvseason'
            qp['url'] = item['url']
            info = utils.video_info(item, {'mediatype': 'season'})
            isdir = True
        if item_type == 'tvepisode':
            action = 'play'
            qp['url'] = item['url']
            info = utils.video_info(item, {'mediatype': 'episode'})
            title = "S%02dE%02d: %s" % (item['parent_seq'], item['seq'], title)
            qp['video'] = 1
        if item_type == 'movie':
            action = 'play'
            info = utils.video_info(item)
            qp['video'] = 1

        if options.get('act') == 'collections':
            action = 'collections'
            isdir = True
            if item.get('slug'):
                qp['id'] = item.get('slug')

            title = item.get('name').encode('utf-8')

        poster = utils.get_item_poster(item, cookie_store.get_asset_host(__settings__), options)
        li = xbmcgui.ListItem(title)
        li.setArt({'thumb': poster, 'poster': poster, 'icon': poster, 'fanart': utils.get_item_fanart(item, cookie_store.get_asset_host(__settings__), options)})
        if info:
            # log("info: %s" % info)
            li.setInfo('Video', info)
            if qp.get('video') == 1 and item.get('watch_progress'):
                li.setProperty('totaltime', str(info['duration']))
                li.setProperty('resumetime', str(item.get('watch_progress')))
        if 'video' in qp and qp['video'] == 1:
            li.setProperty('IsPlayable', 'true')

        link = get_internal_link(action, qp)
        log("link: %s" % link)
        xbmcplugin.addDirectoryItem(handle, link, li, isdir)


def add_default_headings(qp, fmt="slp"):
    if 's' in fmt:
        li = xbmcgui.ListItem('[COLOR FFFFF000]Поиск[/COLOR]')
        xbmcplugin.addDirectoryItem(handle, get_internal_link(qp['act'], qp), li, False)
    if 'l' in fmt:
        li = xbmcgui.ListItem('[COLOR FFFFF000]Последние[/COLOR]')
        xbmcplugin.addDirectoryItem(handle, get_internal_link(qp['act'], qp), li, True)
    if 'p' in fmt:
        li = xbmcgui.ListItem('[COLOR FFFFF000]Популярные[/COLOR]')
        xbmcplugin.addDirectoryItem(handle, get_internal_link('items', addonutils.dict_merge(qp, {'sort': '-rating'})), li, True)
    if 'a' in fmt:
        li = xbmcgui.ListItem('[COLOR FFFFF000]По алфавиту[/COLOR]')
        xbmcplugin.addDirectoryItem(handle, get_internal_link('alphabet', qp), li, True)
    if 'g' in fmt:
        li = xbmcgui.ListItem('[COLOR FFFFF000]Жанры[/COLOR]')
        xbmcplugin.addDirectoryItem(handle, get_internal_link('genres', qp), li, True)


# Form internal link for plugin navigation
def get_internal_link(action, params={}):
    params = urllib.urlencode(params)
    return "%s/%s?%s" % (const.PLUGIN_ID, action, params)


def notice(message, heading="", time=4000):
    xbmc.executebuiltin('XBMC.Notification("%s", "%s", "%s")' % (heading, message, time))


def route(fakeSys=None):
    if fakeSys:
        current = fakeSys.split('?')[0]
        qs = fakeSys.split('?')['?' in fakeSys]
    else:
        current = sys.argv[0]
        qs = sys.argv[2]

    action = current.replace(const.PLUGIN_ID, '').lstrip('/')
    action = action if action else 'login'
    actionFn = 'page' + action.title()
    qp = get_params(qs)

    log("ROUTE:  %s / %s" % (actionFn, str(qp)))
    globals()[actionFn](qp)


# Parse query string params into dict
def get_params(qs):
    params = {}
    if qs:
        qs = qs.replace('?', '').split('/')[-1]
        for i in qs.split('&'):
            if '=' in i:
                k, v = i.split('=')
                params[k] = urllib.unquote_plus(v)
    return params


# Entry point
def init():
    if cookie_store.has_auth(__settings__) and not cookie_store.get_asset_host(__settings__):
        resp = apiGet(const.API_URL + '/api/site_settings')
        asset_host = resp.data.get('asset_host')
        log("Save Asset Host: %s" % asset_host)
        cookie_store.save_asset_host(__settings__, asset_host)

    route()


#######################
#  Actions
#######################

def pageFreeLimit(qp):
    cookie_store.reset(__settings__)
    wn = free_limit.FreeLimitWindow("free_limit.xml", _ADDON_PATH, __skinsdir__, settings=__settings__)
    wn.doModal()
    del wn
    log("showActivationWindow : Close modal auth")


def pageLogin(qp):
    log("pageLogin: %s, %s" % (str(qp), pageLogin))

    local_vars = {
        'was_auth': False
    }

    def onAuth(resp):
        user_id = (resp.data.get('user_id') if resp.data else '')
        __settings__.setSetting("user_id", user_id)
        local_vars['was_auth'] = True
        log("onAuth() was_auth = %s, user_id=%s" % (local_vars['was_auth'], user_id))

    def showActivationWindow():
        log("showActivationWindow : No auth - show login window")
        wn = auth.AuthWindow("auth.xml", _ADDON_PATH, __skinsdir__, settings=__settings__, after_auth=onAuth)
        wn.doModal()
        del wn
        log("showActivationWindow : Close modal auth")

    has_auth = cookie_store.has_auth(__settings__)
    log("has_auth = %s" % has_auth)
    log("cookie_pip = %s" % __settings__.getSetting('cookie_pip'))
    if not has_auth:
        showActivationWindow()
        log("after showActivationWindow(): was_auth = %s" % local_vars['was_auth'])
        if local_vars['was_auth']:
            pageLogin(qp)
        else:
            xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
        return
    else:
        must_select_profile = cookie_store.must_select_profile(__settings__)
        log("must_select_profile = %s" % must_select_profile)
        if must_select_profile:
            pageProfiles(qp)
        else:
            pageIndex(qp)


def apiGet(url, params=None):
    return apiCall('get', url, params)


def apiPost(url, params=None):
    return apiCall('post', url, params)


def apiCall(method, url, params=None):
    if method == 'post':
        resp = api.post_request(__settings__, url, params)
    else:
        resp = api.get_request(__settings__, url, params)

    if resp.statusCode == 302:
        xbmc.executebuiltin("XBMC.Notification(%s, %s, %d, %s)" % ("Authorization Error %s" % resp.statusCode, "Please restart and login again.", 6000, __icon__))
        cookie_store.reset(__settings__)
        xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
    if resp.statusCode == 402:
        pageFreeLimit({})
    elif resp.statusCode != 200:
        error = resp.error or resp.data.get('error')
        log("error: %s" % error)
        if error:
            xbmc.executebuiltin("XBMC.Notification(%s,%s)" % ("Server API Error %s" % resp.statusCode, "API Error %s \"%s\". Please, check your connection or try again later." % (resp.statusCode, resp.error)))
        else:
            xbmc.executebuiltin("XBMC.Notification(%s,%s)" % ("Server API Error %s" % resp.statusCode, "API Error %s. Please, check your connection or try again later." % resp.statusCode))
        cookie_store.reset(__settings__)
        xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
    return resp


def appendWatchProgress(items):
    ids = []
    for item in items:
        if hasattr(item, 'id'):
            ids.append(item['id'])

    if len(ids) > 0:
        watch_progress_resp = apiPost(const.API_URL + '/api/watched', {'ids': ','.join(ids)})
        if watch_progress_resp.statusCode == 200:
            for movie_id in watch_progress_resp.data:
                watch_progress = watch_progress_resp.data[movie_id]
                for movie in items:
                    if movie['id'] == movie_id and watch_progress['resume']['position'] > 0:
                        movie['watch_progress'] = watch_progress['resume']['position']
    return items


def pageProfiles(qp):
    log("pageProfiles. %s" % (str(qp)))

    def selectProfile(profile_id):
        apiGet(const.API_URL + '/account/profiles/set/%s' % profile_id)

    def load_profiles():
        log("Load Profile list")

        profiles_resp = apiGet(const.API_URL + '/account/profiles')
        profile_count = 0
        if profiles_resp.statusCode == 200 and profiles_resp.data.get('items'):
            profiles = profiles_resp.data.get('items')
            xbmcplugin.setContent(handle, 'files')

            for profile in profiles:
                li = xbmcgui.ListItem("Select profile: [COLOR FF00FF00]" + profile.get('name').encode('utf-8') + "[/COLOR]")
                link = get_internal_link('/profiles', {'profile_id': profile.get('id')})
                xbmcplugin.addDirectoryItem(handle=handle, url=link,listitem=li, isFolder=False)
                profile_count = profile_count + 1

            xbmcplugin.endOfDirectory(handle)
            cookie_store.save_profile_count(__settings__, len(profiles))

        else:
            log("Profiles list is empty")
            xbmc.executebuiltin("XBMC.Notification(%s,%s)" % ("Get user info Error" % account_resp.statusCode, "API Error %s \"%s\". Please, check your connection or try again later." % (account_resp.statusCode, account_resp.error)))
            cookie_store.save_profile_count(__settings__, 0)
            pageIndex({})

    if 'profile_id' in qp and qp.get('profile_id'):
        selectProfile(qp.get('profile_id'))
        xbmc.executebuiltin('Container.Update(plugin://' + const.ADDON_ID + '/,replace)')
    else:
        is_switch_profile = qp.get('act') == 'profiles'
        if is_switch_profile:
            load_profiles()

        else:
            account_resp = apiGet(const.API_URL + '/account/api')

            if account_resp.statusCode == 200:
                if account_resp.data.get('show_profile_selection'):
                    load_profiles()
                else:
                    log("No profile to select")
                    cookie_store.save_profile_count(__settings__, 1)
                    pageIndex({})
            else:
                log("Show Account info list load error")
                xbmc.executebuiltin("XBMC.Notification(%s,%s)" % ("Get user Error %s" % account_resp.statusCode, "API Error %s \"%s\". Please, check your connection or try again later." % (account_resp.statusCode, account_resp.error)))
                cookie_store.save_profile_count(__settings__, 0)
                pageIndex({})



# Main screen - show type list
def pageIndex(qp):
    log("pageIndex. %s" % (str(qp)))
    # if 'type' in qp:
    #     add_default_headings(qp, "slpga")
    # else:
    response = apiGet(const.API_URL + '/api/kodi/home')
    if response.statusCode == 200:
        movie_lists = response.data['items']

        show_lists(movie_lists)

    xbmcplugin.endOfDirectory(handle)
    xbmc.executebuiltin('Container.SetViewMode(0)')


def pageFolder(qp):
    log("%s : pageFolder. %s" % (const.PLUGIN_ID, str(qp)))


def pageItems(qp):
    log("pageItems qp=%s" % qp)
    params = {'postersize': 'poster-big', 'p': get_page(qp), 'previewsizes': '{"preview_large":"preview_large"}', 'add_mroot_title': 1}
    if qp.get('act') == 'search':
        params['q'] = qp['q']

    response = apiGet(const.API_URL + qp['url'], params)
    if response.statusCode == 200:
        show_items(appendWatchProgress(response.data['items']), qp)
        show_pagination(response.data, 'items', qp)
        xbmcplugin.endOfDirectory(handle)
    # else:
    #     notice(response.error, qp['title'])


def pageTvshow(qp):
    log("pageTvshow qp=%s" % qp)
    response = apiGet(const.API_URL + qp['url'], {'postersize': 'poster-big'})
    if response.statusCode == 200:
        show_items(response.data['seasons'], {'mroot_poster': utils.get_item_poster(response.data['item'], cookie_store.get_asset_host(__settings__))})
    else:
        notice(response.error, qp['title'])
    xbmcplugin.endOfDirectory(handle)


def pageTvseason(qp):
    log("pageTvseason qp=%s" % qp)
    response = apiGet(const.API_URL + qp['url'], {'postersize': 'poster-big', 'add_mroot_title': 1})
    if response.statusCode == 200:
        show_items(appendWatchProgress(response.data['episodes']))
    else:
        notice(response.error, qp['title'])
    xbmcplugin.endOfDirectory(handle)


def pageList(qp):
    log("pageList qp=%s" % qp)
    response = apiGet(const.API_URL + qp['url'], {'postersize': 'poster-big', 'add_mroot_title': 1})
    if response.statusCode == 200:
        show_lists(appendWatchProgress(response.data['items']))
        xbmcplugin.endOfDirectory(handle)
    # else:
    #     notice(response.error, qp['title'])


def pagePlay(qp):
    log("pagePlay qp: %s" % qp)

    path = '/movies/%s' % qp['id']
    if 'url' in qp and qp['url']:
        path = qp['url']

    resp = apiGet(const.API_URL + path, {'skip_redirect': 1, 'sub': 1})
    if resp.statusCode == 200:
        media = resp.data['item']['media']

        log("resp.data media: %s" % media)

        if 'media' not in resp.data['item'] or len(media) == 0:
            notice("The video temporary unavailable", "Video temporary unavailable", time=8000)
            return
        liObject = xbmcgui.ListItem(resp.data['item']['title'])
        target_quality = ''.join(re.findall(r'\d+', DEFAULT_QUALITY))

        if target_quality in media:
            url = media[target_quality]
        else:
            url = media[media.keys()[0]]

        log("Video URL = %s" % url)
        __settings__.setSetting("last_video_url", const.ADDON_ID + '_' + url)
        __settings__.setSetting("last_video_id", resp.data['item']['id'])
        liObject.setPath(url)
        liObject.setProperty('StartOffset', '601')

        subtitle_urls = []
        if 'subtitles' in resp.data['item']:
            if 'eng' in resp.data['item']['subtitles']:
                for item in resp.data['item']['subtitles']['eng']:
                    # subtitle_urls.append('https://' + item['url'].replace('vtt', 'srt'))
                    subtitle_urls.append('https://' + cookie_store.get_asset_host(__settings__) + item['url'] + '?_=/filename.vtt')

        subtitles_resp = apiGet(const.API_URL + '/account/subtitles/movie/' + resp.data['item']['id'])
        if subtitles_resp.statusCode == 200:
            if 'subtitles' in subtitles_resp.data:
                for item in subtitles_resp.data['subtitles']:
                    subtitle_urls.append('https://' + cookie_store.get_asset_host(__settings__) + item['url'] + '?_=/filename.vtt')

        if len(subtitle_urls) > 0:
            liObject.setSubtitles(subtitle_urls)
            # liObject.addStreamInfo('subtitle', {'language': 'en'})

        xbmcplugin.setResolvedUrl(handle, True, liObject)


def pageSearch(qp):
    log("pageSearch qp: %s" % qp)
    keyboard = xbmc.Keyboard()
    keyboard.setDefault('')
    keyboard.setHeading('Search')
    keyboard.doModal()
    search_string = ''
    if keyboard.isConfirmed():
        search_string = keyboard.getText()
    log("search_string = %s" % search_string)
    if len(search_string.decode('utf-8')) > 0:
        if 'p' in qp:
            qp['p'] = 1
        qp['q'] = search_string
        qp['show_tvshow_at_title'] = True
        pageItems(qp)
    else:
        notice("Search query is empty", "Search")
        # pageIndex(qp)


def pageCollections(qp):
    log("pageCollections: %s" % qp)
    if qp.get('id'):
        qp['act'] = 'collection'
        qp['url'] = '/collections/' + qp.get('id')
    pageItems(qp)
