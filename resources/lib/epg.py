import json
import os
import time
import xbmc
import xbmcaddon
import xbmcvfs

from resources.lib.api import get_channels, check_channel_active

EPG_CACHE_FILE = None


def get_cache_path():
    global EPG_CACHE_FILE
    if EPG_CACHE_FILE is None:
        addon = xbmcaddon.Addon("plugin.video.freehit")
        profile = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
        if not xbmcvfs.exists(profile):
            xbmcvfs.mkdirs(profile)
        EPG_CACHE_FILE = os.path.join(profile, "epg_cache.json")
    return EPG_CACHE_FILE


def get_cache_duration_minutes():
    addon = xbmcaddon.Addon("plugin.video.freehit")
    cache_setting = int(addon.getSetting("epg_cache_minutes") or 1)
    durations = [15, 30, 60, 120]
    return durations[cache_setting]


def load_epg_cache():
    cache_file = get_cache_path()
    try:
        if xbmcvfs.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
    except Exception as e:
        xbmc.log("[Freehit] Error loading EPG cache: {}".format(str(e)), xbmc.LOGWARNING)
    return {"channels": [], "timestamp": 0}


def save_epg_cache(channels):
    cache_file = get_cache_path()
    cache_data = {
        "channels": channels,
        "timestamp": time.time(),
    }
    try:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)
    except Exception as e:
        xbmc.log("[Freehit] Error saving EPG cache: {}".format(str(e)), xbmc.LOGWARNING)


def is_cache_valid():
    cache = load_epg_cache()
    cache_age = time.time() - cache.get("timestamp", 0)
    max_age = get_cache_duration_minutes() * 60
    return cache_age < max_age


def get_epg(source="freehit.eu", force_refresh=False):
    if not force_refresh and is_cache_valid():
        cache = load_epg_cache()
        return cache.get("channels", [])

    channels = get_channels(source)
    if channels:
        save_epg_cache(channels)

    return channels


def build_epg_info(channels):
    epg_items = []
    for channel in channels:
        is_active = check_channel_active(channel)
        epg_items.append({
            "channel_id": channel.get("channelId", 0),
            "caption": channel.get("caption", ""),
            "channel_name": channel.get("channelName", ""),
            "is_active": is_active,
            "fms_url": channel.get("fmsUrl", ""),
            "streams": channel.get("streamsList", []),
        })
    return epg_items


def get_live_matches(channels):
    return [ch for ch in channels if check_channel_active(ch)]


def clear_epg_cache():
    cache_file = get_cache_path()
    try:
        if xbmcvfs.exists(cache_file):
            xbmcvfs.delete(cache_file)
    except Exception as e:
        xbmc.log("[Freehit] Error clearing EPG cache: {}".format(str(e)), xbmc.LOGWARNING)
