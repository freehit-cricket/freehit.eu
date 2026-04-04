import json
import requests
import xbmc
import xbmcaddon

API_BASE = "https://rest.smartcric.stream"
SN = "8cdR-LEJ8-U3FP-X6bc-6a3gc"
AUTH_KEY = "be2e44a53fa58825d650068ffeb24eca22bcf18f7f451c73d10cf1a4b84483b4a"

SOURCES = {
    "freehit.eu": {
        "api_base": "https://rest.smartcric.stream",
        "sn": SN,
        "auth_key": AUTH_KEY,
    },
    "smartcric": {
        "api_base": "https://rest.smartcric.stream",
        "sn": SN,
        "auth_key": AUTH_KEY,
    },
    "touchcric": {
        "api_base": "https://rest.smartcric.stream",
        "sn": SN,
        "auth_key": AUTH_KEY,
    },
}


def get_addon():
    return xbmcaddon.Addon("plugin.video.freehit")


def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://freehit.eu/",
    })
    return session


def get_channels(source="freehit.eu"):
    addon = get_addon()
    source_config = SOURCES.get(source, SOURCES["freehit.eu"])
    url = "{}/mobile/channels/live/{}".format(source_config["api_base"], source_config["sn"])
    timeout = int(addon.getSetting("timeout") or 15)

    try:
        session = get_session()
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("channelsList", [])
    except Exception as e:
        xbmc.log("[Freehit] Error fetching channels: {}".format(str(e)), xbmc.LOGERROR)
        return []


def get_jako_key(auth_key):
    return auth_key[:0x2f] + auth_key[0x30:]


def build_stream_url(fms_url, stream_name, stream_id, jako_key):
    return "https://{}/mobile/{}/playlist.m3u8?id={}&pk={}".format(
        fms_url, stream_name, stream_id, jako_key
    )


def get_streams_for_channel(channel, source="freehit.eu"):
    streams_list = channel.get("streamsList", [])
    if not streams_list:
        return []

    addon = get_addon()
    source_config = SOURCES.get(source, SOURCES["freehit.eu"])
    jako_key = get_jako_key(source_config["auth_key"])

    quality_pref = int(addon.getSetting("stream_quality") or 0)

    streams = []
    for stream in streams_list:
        stream_url = build_stream_url(
            channel.get("fmsUrl", ""),
            stream.get("streamName", ""),
            stream.get("streamId", ""),
            jako_key,
        )
        streams.append({
            "url": stream_url,
            "name": stream.get("streamName", "Stream"),
            "quality": stream.get("caption", ""),
            "stream_id": stream.get("streamId", ""),
        })

    if quality_pref == 1 and streams:
        return [streams[-1]]
    elif quality_pref == 2 and len(streams) > 1:
        mid = len(streams) // 2
        return [streams[mid]]
    elif quality_pref == 3 and streams:
        return [streams[0]]

    return streams


def check_channel_active(channel):
    return channel_has_streams(channel)


def channel_has_streams(channel):
    streams = channel.get("streamsList", [])
    return len(streams) > 0


def get_channel_label(channel):
    caption = channel.get("caption", "")
    is_active = check_channel_active(channel)

    if is_active:
        return "{}  [I][COLOR green]Live[/COLOR][/I]".format(caption)
    else:
        return "{}  [I][COLOR gray]Offline[/COLOR][/I]".format(caption)
