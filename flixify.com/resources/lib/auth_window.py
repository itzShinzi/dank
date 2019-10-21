#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui, xbmcaddon, xbmc
import threading
import re
import const
import api

CLIENT_ID = "xbmc"
CLIENT_SECRET = "in39kdyl4psfoh7eryxfh6pw8vdlpry2"


def log(str):
    xbmc.log("FLX_LOG: AuthWindow: %s" % str)


class Auth(object):
    terminated = False
    timer = 0
    ERROR, PENDING_STATUS, SUCCESS, EXPIRED = range(4)

    def __init__(self, settings, window=None, after_auth=None):
        log("new Auth() after_auth = %s" % after_auth)
        self.window = window
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.settings = settings
        self.afterAuth = after_auth

    def close(self):
        if self.window is not None:
            self.window.close()

    def get_access_token(self):
        return self.settings.getSetting('access_token')

    def set_access_token(self, value):
        if value is not None:
            value = value.encode('utf-8')
        self.settings.setSetting('access_token', value)

    def get_refresh_token(self):
        return self.settings.getSetting('refresh_token')

    def set_refresh_token(self, value):
        if value is not None:
            value = value.encode('utf-8')
        self.settings.setSetting('refresh_token', value)

    access_token = property(get_access_token, set_access_token)
    refresh_token = property(get_refresh_token, set_refresh_token)

    def reauth(self):
        self.access_token = ""
        self.device_token = ""

    def get_device_code(self, url=const.PIN_API_URL):
        log("get_device_code")
        resp = api.get_request(self.settings, url)

        log("resp.error = %s" % resp.error)

        error = resp.error or resp.data.get('error')
        log("error: %s" % error)
        if error:
            xbmc.executebuiltin("XBMC.Notification(%s,%s)" % ("PIN Error %s" % resp.statusCode, "PIN Loading Error %s \"%s\". Please, check your connection or try again later." % (resp.statusCode, resp.error)))
            return self.ERROR, resp

        log("resp.data: %s" % resp.data)

        self.pin_id = resp.data['id'].encode('utf-8')

        return self.SUCCESS, resp

    def check_pin_auth(self, url=const.PIN_CHECK_API_URL):
        log("check_pin_auth")
        # try:
        resp = api.get_request(self.settings, url, {
            'pin_id': self.pin_id
        })

        log("PIN check result: %s %s" % (resp.statusCode, resp.data))

        state = (resp.data.get('state') if resp.data else '')
        error = None if state else resp.error
        if error:
            return self.ERROR, resp
        else:
            if state and state == 'waiting':
                return self.PENDING_STATUS, resp
            elif state and state == 'success':
                return self.SUCCESS, resp
            else:
                return self.PENDING_STATUS, resp

    def wait_for_pin_auth(self, interval, parent):
        while not parent.stopped.wait(1):
            log('wait_for_pin_auth TICK')
            status, resp = self.check_pin_auth()
            if status == self.SUCCESS:
                log("call self.afterAuth")
                self.afterAuth(resp)
                parent.closeWindow()
                return True
            elif status == self.ERROR:
                parent.showError("Server Error: %s" % resp.error)
                return False

            parent.stopped.wait(interval)


class AuthWindow(xbmcgui.WindowXMLDialog):
    was_auth = False

    def __init__(self, *args, **kwargs):
        self.stopped = threading.Event()
        self.auth = Auth(kwargs['settings'], window=self, after_auth=kwargs['after_auth'])

    def onInit(self):
        log("onInit()")
        status, resp = self.auth.get_device_code()
        if status == self.auth.ERROR:
            label = self.getControl(9111)
            label.setLabel("PIN Loading Error %s \"%s\". Please, check your connection or try again later." % (resp.statusCode, resp.error))
            return

        label = self.getControl(9111)
        label.setLabel("Enter this PIN on your account page to authorize this device")
        label = self.getControl(9113)
        label.setLabel(str('-'.join(re.findall('..', str(resp.data['pin'])))).encode('utf-8'))

        t = threading.Thread(target=self.auth.wait_for_pin_auth, args=[5, self])
        t.daemon = True
        t.start()

    def showError(self, error):
        label = self.getControl(9111)
        label.setLabel('')
        label = self.getControl(9112)
        label.setLabel(error)
        label = self.getControl(9113)
        label.setLabel('Please try again later or contact a Support')

    def onAction(self, action):
        buttonCode = action.getButtonCode()
        actionID = action.getId()
        if actionID in [9, 10, 13, 14, 15]:
            self.closeWindow()

    def closeWindow(self):
        self.stopped.set()
        for thread in threading.enumerate():
            if thread.isAlive() and thread != threading.currentThread():
                thread.join(1)
        self.close()
