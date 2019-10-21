#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, xbmc, xbmcaddon

__skinsdir__ = "DefaultSkin"

__id__ = 'flixify.com'
__addon__ = xbmcaddon.Addon(id=__id__)
__settings__ = xbmcaddon.Addon(id=__id__)

_ADDON_PATH = xbmc.translatePath(__addon__.getAddonInfo('path'))
if (sys.platform == 'win32') or (sys.platform == 'win64'):
    _ADDON_PATH = _ADDON_PATH.decode('utf-8')

sys.path.append(os.path.join(_ADDON_PATH, 'resources', 'lib'))
sys.path.append(os.path.join(_ADDON_PATH, 'resources', 'skins'))
sys.path.append(os.path.join(_ADDON_PATH, 'resources', 'skins', __skinsdir__))

import cookie_store as cookie_store
import const


def log(str):
    xbmc.log("%s FLX_LOG: %s" % (const.PLUGIN_ID, str))


log('--------------------------------------- START')

if not cookie_store.has_auth(__settings__):
    cookie_store.reset(__settings__)
else:
    try:
        reset_auth = int(__settings__.getSetting('reset_auth'))
    except:
        reset_auth = 0

    if reset_auth == 1:
        cookie_store.reset(__settings__)

if __name__ == '__main__':
    import addon_main_worker

    addon_main_worker.init()
