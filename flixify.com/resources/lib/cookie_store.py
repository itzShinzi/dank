import json
import cookielib
import xbmc


def log(str):
    # xbmc.log("FLX_LOG: CookieStore: %s" % str)
    pass


def logDebug(str):
    xbmc.log("FLX_LOG: CookieStore: %s" % str)
    pass


auth_version = '100'

cookies_to_store = ['pip', 'session', 'profile_id']
cookies_to_auth = ['pip', 'session']

cookie_fields = [
    'version',
    'value',
    'port',
    'domain',
    'path',
    'secure',
    'expires',
    'discard'
]


def get_cookie_by_name(cj, name):
    for cookie in cj:
        if cookie.name == name: return cookie
    return None


def store_cookies(settings, cj):
    settings.setSetting('auth_ver', auth_version)
    for cookie_name in cookies_to_store:
        cookie = get_cookie_by_name(cj, cookie_name)
        if cookie is None:
            store_cookie(settings, cookie_name)
        else:
            store_cookie(settings, cookie_name, cookie)


def get_setting_name(cookie_name):
    return 'cookie_' + cookie_name


def store_cookie(settings, cookie_name, cookie=None):
    cookie_str = ''
    if cookie is not None:
        cookie_values = []
        for field_name in cookie_fields:
            if hasattr(cookie, field_name):
                val = getattr(cookie, field_name)
            else:
                val = 0

            # if field_name == 'val' and val == None: val = -1
            # if field_name == 'port' and val == None: val = -1
            # if field_name == 'secure': val = (1 if val == True else 0)
            # if field_name == 'discard': val = (1 if val == True else 0)

            cookie_values.append(val)

        cookie_str = json.dumps(cookie_values)

    log('store cookie "%s" to %s: %s' % (get_setting_name(cookie_name), settings, cookie_str))
    settings.setSetting(get_setting_name(cookie_name), cookie_str)


def restore_cookie(settings, cookie_name):
    cookie_str = settings.getSetting(get_setting_name(cookie_name))
    log("restore_cookie %s from %s: %s" % (get_setting_name(cookie_name), settings, cookie_str))
    if cookie_str:
        cookie_values = json.loads(cookie_str)

        result = dict(
            version=0,
            name=cookie_name,
            value=None,
            port=None,
            domain='',
            path='/',
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={'HttpOnly': None},
            rfc2109=False, )
        for idx, field_name in enumerate(cookie_fields):
            val = cookie_values[idx]
            result[field_name] = val

        result['port_specified'] = bool(result['port'])
        result['domain_specified'] = bool(result['domain'])
        result['domain_initial_dot'] = result['domain'].startswith('.')
        result['path_specified'] = bool(result['path'])
        return cookielib.Cookie(**result)
    else:
        return None


def restore_cookies(settings, cj):
    for cookie_name in cookies_to_store:
        cookie = restore_cookie(settings, cookie_name)
        if cookie is not None:
            cj.set_cookie(cookie)
    return cj


def reset(settings):
    log("RESET")
    for cookie_name in cookies_to_store:
        settings.setSetting(get_setting_name(cookie_name), None)
    settings.setSetting('auth_ver', None)
    settings.setSetting('user_id', None)
    settings.setSetting('last_video_url', None)
    settings.setSetting('last_video_id', None)
    settings.setSetting('reset_auth', '0')
    settings.setSetting('profiles_count', None)
    settings.setSetting('asset_host', None)


def has_auth(settings):
    log("has_auth...")
    has_all_cookies = True
    last_auth_ver = settings.getSetting('auth_ver')
    if last_auth_ver != auth_version:
        return False
    for cookie_name in cookies_to_auth:
        cookie = restore_cookie(settings, cookie_name)
        log("Cookie %s, exp=%s: %s" % (cookie_name, str(cookie.is_expired()) if cookie else 'None', cookie))
        if cookie:
            has_all_cookies = has_all_cookies and not cookie.is_expired()
        else:
            has_all_cookies = False
    return has_all_cookies


def must_select_profile(settings):
    logDebug("SETTINGS profiles_count = %s, profile_id cookie = %s" % (settings.getSetting('profiles_count'), restore_cookie(settings, 'profile_id')))
    if settings.getSetting('profiles_count') is None or (settings.getSetting('profiles_count') == ''):
        return True
    else:
        return int(settings.getSetting('profiles_count')) > 1 and not restore_cookie(settings, 'profile_id')


def has_multiple_profiles(settings):
    return int(settings.getSetting('profiles_count')) > 1


def save_profile_count(settings, count):
    logDebug("save_profile_count: %s" % count)
    settings.setSetting('profiles_count', str(count))


def save_asset_host(settings, host):
    logDebug("save_asset_host: %s" % host)
    settings.setSetting('asset_host', str(host))


def get_asset_host(settings):
    return settings.getSetting('asset_host')

