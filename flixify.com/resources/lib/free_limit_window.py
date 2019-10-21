#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui, xbmcaddon, xbmc


def log(str):
    xbmc.log("FLX_LOG: FreeLimitWindow: %s" % str)


class FreeLimitWindow(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        log("FreeLimitWindow()")

    def onInit(self):
        log("onInit()")

    def onAction(self, action):
        actionID = action.getId()
        if actionID in [9, 10, 13, 14, 15]:
            self.closeWindow()

    def closeWindow(self):
        self.close()
        xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
        log("closeWindow")
