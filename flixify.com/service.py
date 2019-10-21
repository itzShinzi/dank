import time
import datetime
import os
import xbmc
import math
import xbmcaddon

__id__ = 'flixify.com'
__addon__ = xbmcaddon.Addon(id=__id__)

_ADDON_PATH = xbmc.translatePath(__addon__.getAddonInfo('path'))
if (sys.platform == 'win32') or (sys.platform == 'win64'):
    _ADDON_PATH = _ADDON_PATH.decode('utf-8')

sys.path.append(os.path.join(_ADDON_PATH, 'resources', 'lib'))

import api
import const


def log(s):
    xbmc.log("%s FLX_LOG SERVICE: %s" % (__id__, s))


my_id = datetime.datetime.now()
last_tracked_url = None
watch_time_buffer = 0
watch_time_buffer_total = 0
last_watch_position = -1
total_time = 0

last_movie_save_cw_limit_sec = 0
SAVE_CW_LIMIT_SEC = 2 * 60


def send_watch_time():
    global watch_time_buffer, last_movie_save_cw_limit_sec

    if watch_time_buffer > 1:
        watched_delta = math.fabs(watch_time_buffer)
        watch_time_buffer -= watched_delta

        last_video_id = __addon__.getSetting('last_video_id')
        user_id = __addon__.getSetting('user_id')

        last_movie_save_cw_limit_sec -= watched_delta

        if user_id and last_video_id:
            params = {'pos': round(last_watch_position, 2), 'user_id': user_id, 'delta_sec': round(watched_delta, 2)}
            if watch_time_buffer_total > 30 and last_movie_save_cw_limit_sec <= 0:
                params['cw'] = 1
                last_movie_save_cw_limit_sec = SAVE_CW_LIMIT_SEC

            if total_time and last_watch_position > total_time * 0.92:
                params['completed'] = 1

            api.post_request(__addon__, api.append_params_to_url(const.API_URL + '/account/watched/seen/' + last_video_id, params))


if __name__ == '__main__':
    monitor = xbmc.Monitor()

    while not monitor.abortRequested():
        if xbmc.Player().isPlayingVideo():

            file_url = xbmc.Player().getPlayingFile()
            last_video_url = __addon__.getSetting('last_video_url')
            pos = xbmc.Player().getTime()
            total_time = xbmc.Player().getTotalTime()

            # Track only videos of my addon
            if __id__ + '_' + file_url == last_video_url:
                # Reset if video changed
                if last_tracked_url != file_url:
                    watch_time_buffer = 0
                    watch_time_buffer_total = 0
                    last_watch_position = pos
                    last_tracked_url = file_url
                else:
                    pass_time = math.fabs(pos - last_watch_position)
                    last_watch_position = pos
                    # Ignore cases with > 3 sec (step of checkin is 1 sec)
                    if pass_time > 3:
                        watch_time_buffer = 0
                        last_watch_position = pos
                    else:
                        watch_time_buffer += pass_time
                        watch_time_buffer_total += pass_time

                # log("IS_PLAYING: pos=%s watch_time_buffer=%s watch_time_buffer_total=%s last_watch_position=%s" % (pos, watch_time_buffer, watch_time_buffer_total, last_watch_position))

            if watch_time_buffer > 15:
                send_watch_time()

        elif watch_time_buffer > 1:
            send_watch_time()

        if monitor.waitForAbort(1):
            # Abort was requested while waiting. We should exit
            # log("Abort was requested while waiting. We should exit %s" % my_id)
            break

