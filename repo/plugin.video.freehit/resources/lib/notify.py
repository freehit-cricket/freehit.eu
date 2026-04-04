import time
import xbmc
import xbmcaddon
import xbmcgui

from resources.lib.api import get_channels, check_channel_active
from resources.lib.epg import load_epg_cache, get_epg

NOTIFICATION_STATE_FILE = None


def get_state_path():
    global NOTIFICATION_STATE_FILE
    if NOTIFICATION_STATE_FILE is None:
        import os
        import xbmcvfs
        addon = xbmcaddon.Addon("plugin.video.freehit")
        profile = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
        if not xbmcvfs.exists(profile):
            xbmcvfs.mkdirs(profile)
        NOTIFICATION_STATE_FILE = os.path.join(profile, "notification_state.json")
    return NOTIFICATION_STATE_FILE


def load_notification_state():
    state_file = get_state_path()
    try:
        with open(state_file, "r") as f:
            import json
            return json.load(f)
    except Exception:
        return {"notified_channels": [], "last_check": 0}


def save_notification_state(state):
    state_file = get_state_path()
    try:
        import json
        with open(state_file, "w") as f:
            json.dump(state, f)
    except Exception as e:
        xbmc.log("[Freehit] Error saving notification state: {}".format(str(e)), xbmc.LOGWARNING)


def get_check_interval_seconds():
    addon = xbmcaddon.Addon("plugin.video.freehit")
    interval_setting = int(addon.getSetting("notification_interval") or 1)
    intervals = [60, 120, 300, 600]
    return intervals[interval_setting]


def should_notify():
    state = load_notification_state()
    last_check = state.get("last_check", 0)
    interval = get_check_interval_seconds()
    return (time.time() - last_check) >= interval


def update_last_check():
    state = load_notification_state()
    state["last_check"] = time.time()
    save_notification_state(state)


def notify_live_match(channel):
    addon = xbmcaddon.Addon("plugin.video.freehit")
    use_sound = addon.getSetting("notification_sound") == "true"

    caption = channel.get("caption", "Live Match")

    message = "Now Live: {}".format(caption)

    icon = addon.getAddonInfo("icon")
    display_time = 10000

    if use_sound:
        xbmcgui.Dialog().notification(
            "Freehit",
            message,
            icon,
            display_time,
            sound=True,
        )
    else:
        xbmcgui.Dialog().notification(
            "Freehit",
            message,
            icon,
            display_time,
            sound=False,
        )

    xbmc.log("[Freehit] Notification: {}".format(message), xbmc.LOGINFO)


def check_and_notify(source="freehit.eu"):
    if not should_notify():
        return

    update_last_check()

    addon = xbmcaddon.Addon("plugin.video.freehit")
    if addon.getSetting("enable_notifications") != "true":
        return

    channels = get_epg(source)
    if not channels:
        return

    state = load_notification_state()
    notified = set(state.get("notified_channels", []))

    new_notifications = False
    for channel in channels:
        if check_channel_active(channel):
            channel_id = channel.get("channelId", 0)
            if channel_id not in notified:
                notify_live_match(channel)
                notified.add(channel_id)
                new_notifications = True

    state["notified_channels"] = list(notified)
    save_notification_state(state)


def reset_notification_state():
    save_notification_state({"notified_channels": [], "last_check": 0})
