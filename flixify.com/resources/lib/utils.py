#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from datetime import datetime
import time


def log(str):
    xbmc.log("FLX_LOG UTILS: %s" % str)


def dict_merge(old, new):
    n = old.copy()
    n.update(new)
    return n


# Get media link
def get_mlink(video, quality='480p', streamType='http'):
    # Normalize quality param
    def normalize(qual):
        qual = str(qual)
        return int(qual.lower().replace('p', '').replace('3d', '1080'))

    qualities = [480, 720, 1080]
    url = ""
    files = video['files']
    files = sorted(files, key=lambda x: normalize(x['quality']), reverse=False)

    # check if auto quality
    if quality.lower() == 'auto':
        return files[-1]['url'][streamType]

    # manual param quality
    for f in files:
        f['quality'] = normalize(f['quality'])
        if f['quality'] == quality:
            return f['url'][streamType]

    for f in reversed(files):
        if normalize(f['quality']) <= normalize(quality):
            return f['url'][streamType]
        url = f['url'][streamType]
    return url


def get_item_poster(item, asset_host, options={}):
    if 'images' in item:
        if item['type'] == 'tvepisode':
            if 'preview' in item['images'] and item['images']['preview']:
                return 'https://' + asset_host + item['images']['preview']
        if 'poster' in item['images'] and item['images']['poster']:
            return 'https://' + asset_host + item['images']['poster']
        if 'mroot_poster' in options and options['mroot_poster']:
            return options['mroot_poster']
        if 'preview_large' in item['images'] and item['images']['preview_large']:
            return 'https://' + asset_host + item['images']['preview_large']
    return None


def get_item_fanart(item, asset_host, options={}):
    if 'images' in item:
        if 'preview_large' in item['images'] and item['images']['preview_large']:
            return 'https://' + asset_host + item['images']['preview_large']
    return None


def video_info(item, extend=None):
    info = {
        'year': int(item['year']) if item['year'] else None,
        'title': item['title'],
    }

    if 'description' in item and item['description']:
        info['plot'] = item['description']
        info['plotoutline'] = item['description']
    if 'certification' in item and item['certification']:
        info['mpaa'] = item['certification']
    if 'duration' in item and item['duration']:
        info['duration'] = item['duration']
    if 'rating' in item and item['rating']:
        info['rating'] = item['rating']
    if 'year' in item and item['year']:
        info['year'] = item['year']
    if 'released_sec_ago' in item and item['released_sec_ago']:
        info['dateadded'] = datetime.fromtimestamp(time.time() - item['released_sec_ago']).strftime('%Y-%m-%d %H:%M:%S')
    if 'genres' in item and item['genres']:
        info['genre'] = []
        for genre in item['genres']:
            info['genre'].append(genre)

    if 'tvshow_title' in item and item['tvshow_title']:
        info['tvshowtitle'] = item['tvshow_title']

    if extend and type(extend) is dict:
        n = info.copy()
        n.update(extend)
        info = n
    return info
