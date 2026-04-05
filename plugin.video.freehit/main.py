import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.api import (
    get_channels,
    get_streams_for_channel,
    check_channel_active,
    channel_has_streams,
    get_channel_label,
    SOURCES,
)
from resources.lib.epg import get_epg, build_epg_info, clear_epg_cache
from resources.lib.notify import check_and_notify

BASE_URL = sys.argv[0]
HANDLE = int(sys.argv[1])
PARAMS = dict(arg.split("=") for arg in sys.argv[2][1:].split("&") if "=" in arg)


def get_setting_bool(key, default=True):
    val = xbmcaddon.Addon("plugin.video.freehit").getSetting(key)
    if val == "":
        return default
    return val == "true"


def add_directory_item(label, url, is_folder=True, info=None, art=None, context=None):
    li = xbmcgui.ListItem(label=label, offscreen=True)
    li.setIsFolder(is_folder)
    if info:
        li.setInfo("video", info)
    if art:
        li.setArt(art)
    if context:
        li.addContextMenuItems(context)
    xbmcplugin.addDirectoryItem(HANDLE, url, li, is_folder)


def add_stream_item(label, url, info=None, art=None):
    li = xbmcgui.ListItem(label=label, path=url, offscreen=True)
    li.setProperty("IsPlayable", "true")
    if info:
        li.setInfo("video", info)
    if art:
        li.setArt(art)

    xbmcplugin.addDirectoryItem(HANDLE, url, li, False)


def get_sources():
    addon = xbmcaddon.Addon("plugin.video.freehit")
    primary_idx = int(addon.getSetting("primary_source") or 0)
    source_keys = ["freehit.eu", "smartcric", "touchcric"]
    primary = source_keys[primary_idx] if primary_idx < len(source_keys) else "freehit.eu"

    if addon.getSetting("fallback_sources") == "true":
        return source_keys
    return [primary]


def show_sources():
    sources = get_sources()
    if len(sources) == 1:
        show_channels(sources[0])
        return

    for source_key in sources:
        source_config = SOURCES.get(source_key, SOURCES["freehit.eu"])
        label = source_key
        url = "{}?action=channels&source={}".format(BASE_URL, source_key)
        add_directory_item(
            label,
            url,
            is_folder=True,
            info={"title": label},
            art={"icon": "DefaultFolder.png"},
        )
    xbmcplugin.endOfDirectory(HANDLE)


def show_channels(source="freehit.eu"):
    channels = get_epg(source)
    if not channels:
        xbmcgui.Dialog().notification(
            "Freehit",
            "Failed to load channels. Check your connection.",
            xbmcaddon.Addon("plugin.video.freehit").getAddonInfo("icon"),
            5000,
        )
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return

    show_offline = get_setting_bool("show_offline_channels")

    context_menu = [
        ("Refresh EPG", "Container.Refresh"),
        ("Clear EPG Cache", "RunPlugin({}?action=clear_cache&source={})".format(BASE_URL, source)),
    ]

    for channel in channels:
        is_active = check_channel_active(channel)
        if not is_active and not show_offline:
            continue

        label = get_channel_label(channel)
        channel_id = channel.get("channelId", 0)
        url = "{}?action=streams&channel_id={}&source={}".format(BASE_URL, channel_id, source)

        info = {
            "title": channel.get("caption", ""),
        }

        add_directory_item(
            label,
            url,
            is_folder=True,
            info=info,
            art={"icon": "DefaultVideo.png"},
            context=context_menu,
        )

    xbmcplugin.setContent(HANDLE, "files")
    xbmcplugin.endOfDirectory(HANDLE)


def show_streams(channel_id, source="freehit.eu"):
    channels = get_epg(source)
    channel = None
    for ch in channels:
        if str(ch.get("channelId", "")) == str(channel_id):
            channel = ch
            break

    if not channel:
        xbmcgui.Dialog().notification(
            "Freehit",
            "Channel not found.",
            xbmcaddon.Addon("plugin.video.freehit").getAddonInfo("icon"),
            5000,
        )
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return

    if not channel_has_streams(channel):
        xbmcgui.Dialog().ok(
            "Freehit",
            "{} is currently offline.".format(channel.get("caption", "Channel"))
        )
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return

    streams = get_streams_for_channel(channel, source)
    if not streams:
        xbmcgui.Dialog().notification(
            "Freehit",
            "No streams available for this channel.",
            xbmcaddon.Addon("plugin.video.freehit").getAddonInfo("icon"),
            5000,
        )
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return

    for stream in streams:
        quality = stream.get("quality") or stream.get("name", "Stream")
        label = "{} - {}".format(channel.get("caption", ""), quality)
        info = {
            "title": label,
        }
        add_stream_item(label, stream["url"], info=info)

    xbmcplugin.setContent(HANDLE, "files")
    xbmcplugin.endOfDirectory(HANDLE)


def play_stream(url):
    li = xbmcgui.ListItem(path=url, offscreen=True)
    li.setProperty("IsPlayable", "true")
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def clear_cache(source="freehit.eu"):
    clear_epg_cache()
    xbmcgui.Dialog().notification(
        "Freehit",
        "EPG cache cleared.",
        xbmcaddon.Addon("plugin.video.freehit").getAddonInfo("icon"),
        3000,
    )


def clear_all_cache():
    clear_epg_cache()
    from resources.lib.notify import reset_notification_state
    reset_notification_state()
    xbmcgui.Dialog().notification(
        "Freehit",
        "All cache cleared.",
        xbmcaddon.Addon("plugin.video.freehit").getAddonInfo("icon"),
        3000,
    )


def router():
    action = PARAMS.get("action", "sources")
    source = PARAMS.get("source", "freehit.eu")
    channel_id = PARAMS.get("channel_id", None)

    actions = {
        "sources": show_sources,
        "channels": lambda: show_channels(source),
        "streams": lambda: show_streams(channel_id, source),
        "clear_cache": lambda: clear_cache(source),
        "clear_all_cache": clear_all_cache,
    }

    handler = actions.get(action)
    if handler:
        handler()
    else:
        show_sources()


if __name__ == "__main__":
    router()
