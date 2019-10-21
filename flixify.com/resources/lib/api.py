import xbmc, xbmcaddon
import urllib2, urllib
import json
import time
import cookielib
import cookie_store as cookie_store


def log(str):
    xbmc.log("FLX_LOG Api: %s" % str)


# noinspection PyUnresolvedReferences
try: # check whether python knows about 'basestring'
    basestring
except NameError: # no, it doesn't (it's Python3); use 'str' instead
    basestring=str


def is_string(obj):
    return isinstance(obj, basestring)


class NoRedirection(urllib2.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

    https_response = http_response


class ApiResp:
    def __init__(self, status_code, data=None, error=None):
        self.statusCode = status_code
        self.data = data
        self.error = error


def pretty_print_POST(self, req):
    log('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


def append_params_to_url(url, params):
    if params:
        url = url + ('&' if '?' in url else '?') + urllib.urlencode(params)
    return url


def get_request(settings, url, params=None):
    url = append_params_to_url(url, params)
    return __request(settings, url)


def post_request(settings, url, params=None):

    if params is not None:
        params = urllib.urlencode(params)
    else:
        params = {"_": time.time()}
    return __request(settings, url, params)


def __request(settings, url, post_data=None, timeout=600):
    url = url + ('&' if '?' in url else '?') + "_=" + str(time.time())
    method = 'GET'
    if post_data:
        method = 'POST'
    log("REQUEST %s URL=%s" % (method, url))
    if post_data:
        log("REQUEST POST DATA: %s" % post_data)

    try:
        cj = cookie_store.restore_cookies(settings, cookielib.CookieJar())

        opener = urllib2.build_opener(NoRedirection, urllib2.HTTPCookieProcessor(cj))
        headers = {'User-Agent': 'PP-base Kodi plugin %s' % settings.getAddonInfo('version'), 'Accept': 'application/json'}


        req = urllib2.Request(url=url, data=post_data, headers=headers)

        # pretty_print_POST(req.prepare())
        log("REQ HEADERS: %s" % req.header_items())
        # log("REQ COOKIES: %s" % cj)
        resp = opener.open(req, timeout=timeout)
        # log("RESP INFO: %s" % resp.info())

        resp_code = resp.code
        resp_data = None
        try:
            resp_data = resp.read()
            if resp:
                resp = json.loads(resp_data)
            else:
                resp = resp_data
        except:
            resp = {}
            pass

        if resp_code != 200:
            log("RESP FAIL %s: %s" % (str(resp_code), ((resp_data[:256] + '..') if len(resp_data) > 75 else resp_data)))
            # log("RESP FAIL INFO: %s" % resp.info())
            return ApiResp(resp_code, resp, 'Unknown error')

        log("RESP %s: %s" % (str(resp_code), ((resp[:256] + '..') if len(resp) > 75 else resp)))

        cookie_store.store_cookies(settings, cj)


        return ApiResp(resp_code, resp)

    except urllib2.URLError as e:
        try:
            body = ''.join(e.readlines())
            if body:
                result = json.loads(body)
                if result['message']:
                    return ApiResp(e.code, None, str(result['message']))
        except:
            pass

        return ApiResp(-1, None, 'Unknown error')

    except Exception as e:
        return ApiResp(-1, None, e)

    xbmc.executebuiltin("XBMC.Notification(%s,%s)" % ("Internet problems", "Connection timed out!"))
