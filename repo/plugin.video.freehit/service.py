import time
import xbmc
import xbmcaddon

from resources.lib.notify import check_and_notify, reset_notification_state

CHECK_INTERVAL = 60
MONITOR = xbmc.Monitor()


class NotificationService:
    def __init__(self):
        self.addon = xbmcaddon.Addon("plugin.video.freehit")
        self.last_check = 0

    def get_check_interval(self):
        interval_setting = int(self.addon.getSetting("notification_interval") or 1)
        intervals = [60, 120, 300, 600]
        return intervals[interval_setting]

    def run(self):
        xbmc.log("[Freehit] Notification service started", xbmc.LOGINFO)

        reset_notification_state()

        while not MONITOR.abortRequested():
            if MONITOR.waitForAbort(CHECK_INTERVAL):
                break

            if self.addon.getSetting("enable_notifications") != "true":
                continue

            try:
                sources_to_check = self.get_sources()

                for source in sources_to_check:
                    check_and_notify(source)
                    if MONITOR.abortRequested():
                        break
            except Exception as e:
                xbmc.log("[Freehit] Notification service error: {}".format(str(e)), xbmc.LOGERROR)

        xbmc.log("[Freehit] Notification service stopped", xbmc.LOGINFO)

    def get_sources(self):
        primary_idx = int(self.addon.getSetting("primary_source") or 0)
        source_keys = ["freehit.eu", "smartcric", "touchcric"]
        primary = source_keys[primary_idx] if primary_idx < len(source_keys) else "freehit.eu"

        if self.addon.getSetting("fallback_sources") == "true":
            return [primary] + [s for s in source_keys if s != primary]
        return [primary]


if __name__ == "__main__":
    service = NotificationService()
    service.run()
