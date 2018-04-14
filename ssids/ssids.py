#!/usr/bin/env python
import sys
import time
import os
import logging

import gi
gi.require_version("NM", "1.0")
from gi.repository import NM, GLib

FORMATTER = logging.Formatter("%(asctime)s — %(message)s")

def create_logger():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    return logger

LOGGER = create_logger()

def debug(*args):
    LOGGER.debug(" ".join([str(arg) for arg in args]))

def set_nm_log_level(level):
    nmc = NM.Client.new(None)

    debug("Setting NetworkManager log level to", level)    

    nmc.set_logging(level, "all")

def set_wpa_log_level(level):
    debug("Setting wpa_supplicant log level to", level)

    if level == "msgdump":
        os.system("dbus-send --print-reply --system --dest=fi.w1.wpa_supplicant1 " \
            "/fi/w1/wpa_supplicant1 org.freedesktop.DBus.Properties.Set " \
            "string:fi.w1.wpa_supplicant1 string:DebugTimestamp variant:boolean:true")

    os.system("dbus-send --print-reply --system --dest=fi.w1.wpa_supplicant1 " \
        "/fi/w1/wpa_supplicant1 org.freedesktop.DBus.Properties.Set " \
        "string:fi.w1.wpa_supplicant1 string:DebugLevel variant:string:{}".format(level))

def restart_network_manager():
    debug("Restarting NetworkManager...")

    os.system("dbus-send --print-reply --system --dest=org.freedesktop.systemd1 " \
        "/org/freedesktop/systemd1 org.freedesktop.systemd1.Manager.RestartUnit " \
        "string:NetworkManager.service string:replace")

def get_device():
    nmc = NM.Client.new(None)
    devices = nmc.get_devices()
    for device in devices:
        if device.get_device_type() == NM.DeviceType.WIFI:
            return device

    sys.exit("WiFi device not found")

def get_access_point_count():
    count = len(get_device().get_access_points())

    debug("Access point count:", count)

    return count

def request_scan():
    device = get_device()

    debug("WiFi scan requested")

    try:
        device.request_scan()
    except GLib.Error as e:
        debug(e.message)

def ssid_to_utf8(ap):
    ssid = ap.get_ssid()
    if not ssid:
        return ""
    return NM.utils_ssid_to_utf8(ap.get_ssid().get_data())

def print_device_info():
    device = get_device()
    debug("Device:", device.get_iface())
    debug("Driver:", device.get_driver())
    debug("Driver version:", device.get_driver_version())
    debug("Firmware version:", device.get_firmware_version())

def print_ap_info():
    device = get_device()
    active_ap = device.get_active_access_point()
    ssid = None
    if active_ap is not None:
        ssid = ssid_to_utf8(active_ap)

    debug("Active AP:", ssid)

def set_managed(managed):
    if managed:
        debug("Switching to managed...")
    else:
        debug("Switching to unmanaged...")
        
    device = get_device()
    device.set_managed(managed)


def cleanup():
    set_nm_log_level("info")
    set_wpa_log_level("info")

    debug("Exiting...")

    sys.exit(0)

def wait(seconds):
    debug("Sleeping", seconds, "seconds...")

    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        cleanup()


def main():
    set_nm_log_level("trace")
    set_wpa_log_level("msgdump")

    print_device_info()

    while True:
        wait(10)

        print_ap_info()

        count = get_access_point_count()

        if count > 0:
            continue
        
        debug("No access points available")

        request_scan()

        wait(10)

        count = get_access_point_count()

        if count > 0:
            debug("Scanning WORKED!!!")
            continue

        debug("Scanning did NOT work")

        cleanup()

        set_managed(False)

        wait(5)

        set_managed(True)

        wait(10)

        count = get_access_point_count()

        if count > 0:
            debug("Unmanaged/managed WORKED!!!")
            continue

        debug("Unmanaged/managed did NOT work")

        restart_network_manager()

        time.sleep(10)

        count = get_access_point_count()

        if count > 0:
            debug("Restarting NetworkManager WORKED!!!")
            continue

        debug("Restarting NetworkManager did NOT work")

        cleanup()


if __name__ == "__main__":
    main()
