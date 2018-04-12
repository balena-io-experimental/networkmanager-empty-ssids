#!/usr/bin/env python
import sys
import time
import os
import logging

import gi
gi.require_version("NM", "1.0")
from gi.repository import NM

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

def set_nm_log_level(nmc, level):
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

def get_interface():
    if len(sys.argv) < 2:
        debug("No interface specified as first argument, defaulting to wlan0")
        return "wlan0"
    
    interface = sys.argv[1]
    debug("Target interface:", interface)
    return interface

def get_device(nmc, interface):
    device = nmc.get_device_by_iface(interface)

    if device is None:
        sys.exit("Interface not found: {}".format(interface))

    print_device_info(device)

    return device

def get_access_point_count(device):
    count = len(device.get_access_points())

    debug("Access point count:", count)

    return count

def request_scan(device):
    device.request_scan()

    debug("WiFi scan requested")

def ssid_to_utf8(ap):
    ssid = ap.get_ssid()
    if not ssid:
        return ""
    return NM.utils_ssid_to_utf8(ap.get_ssid().get_data())

def print_device_info(device):
    debug("Device:", device.get_iface())
    debug("Driver:", device.get_driver())
    debug("Driver version:", device.get_driver_version())
    debug("Firmware version:", device.get_firmware_version())

def print_ap_info(device):
    active_ap = device.get_active_access_point()
    ssid = None
    if active_ap is not None:
        ssid = ssid_to_utf8(active_ap)

    debug("Active AP:", ssid)

def cleanup(nmc):
    set_nm_log_level(nmc, "info")
    set_wpa_log_level("info")

    debug("Exiting...")

    sys.exit(0)

def wait(nmc, seconds):
    debug("Sleeping", seconds, "seconds...")

    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        cleanup(nmc)


def main():
    interface = get_interface()

    nmc = NM.Client.new(None)

    set_nm_log_level(nmc, "trace")
    set_wpa_log_level("msgdump")

    device = get_device(nmc, interface)

    while True:
        wait(nmc, 10)

        print_ap_info(device)

        count = get_access_point_count(device)

        if count > 0:
            continue
        
        debug("No access points available")

        wait(nmc, 10)

        debug("Still no access points available")

        request_scan(device)

        wait(nmc, 10)

        count = get_access_point_count(device)

        if count > 0:
            debug("Scanning WORKED!!!")
            continue

        debug("Scanning did NOT work")

        debug("Switching to unmanaged...")

        device.set_managed(False)

        wait(nmc, 5)

        debug("Switching back to managed...")

        device.set_managed(True)

        wait(nmc, 10)

        count = get_access_point_count(device)

        if count > 0:
            debug("Unmanaged/managed WORKED!!!")
            continue

        debug("Unmanaged/managed did NOT work")

        restart_network_manager()

        time.sleep(10)

        nmc = NM.Client.new(None)

        device = get_device(nmc, interface)

        count = get_access_point_count(device)

        if count > 0:
            debug("Restarting NetworkManager WORKED!!!")
            continue

        debug("Restarting NetworkManager did NOT work")

        cleanup(nmc)


if __name__ == "__main__":
    main()
