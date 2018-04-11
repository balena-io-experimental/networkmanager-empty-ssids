#!/usr/bin/env python
import sys
import time
import os

import gi
gi.require_version('NM', '1.0')
from gi.repository import NM

def set_nm_log_level(nmc, level):
    nmc.set_logging(level, "all")

    print("NetworkManager log level set to", level)    

def set_wpa_log_level(level):
    if level == "msgdump":
        os.system('dbus-send --system --dest=fi.w1.wpa_supplicant1 ' \
            '/fi/w1/wpa_supplicant1 org.freedesktop.DBus.Properties.Set ' \
            'string:fi.w1.wpa_supplicant1 string:DebugTimestamp variant:boolean:true')

    os.system('dbus-send --system --dest=fi.w1.wpa_supplicant1 ' \
        '/fi/w1/wpa_supplicant1 org.freedesktop.DBus.Properties.Set ' \
        'string:fi.w1.wpa_supplicant1 string:DebugLevel variant:string:"{}"'.format(level))

    print("wpa_supplicant log level set to", level)

def get_interface():
    if len(sys.argv) < 2:
        print("No interface specified as first argument, defaulting to wlan0")
        return "wlan0"
    
    interface = sys.argv[1]
    print("Target interface:", interface)
    return interface

def get_device(nmc, interface):
    device = nmc.get_device_by_iface(interface)

    if device is None:
        sys.exit("Interface not found: {}".format(interface))

    print_device_info(device)

    return device

def get_access_point_count(device):
    count = len(device.get_access_points())

    print("Access point count:", count)

    return count

def request_scan(device):
    device.request_scan()

    print("WiFi scan requested")

def ssid_to_utf8(ap):
    ssid = ap.get_ssid()
    if not ssid:
        return ""
    return NM.utils_ssid_to_utf8(ap.get_ssid().get_data())

def print_device_info(device):
    active_ap = device.get_active_access_point()
    ssid = None
    if active_ap is not None:
        ssid = ssid_to_utf8(active_ap)
    info = "Device: %s | Driver: %s | Active AP: %s" % (device.get_iface(), device.get_driver(), ssid)
    print(info)

def print_ap_info(device):
    active_ap = device.get_active_access_point()
    ssid = None
    if active_ap is not None:
        ssid = ssid_to_utf8(active_ap)
    info = "Active AP: %s" % (ssid, )
    print(info)

def main():

    interface = get_interface()

    nmc = NM.Client.new(None)

    set_nm_log_level(nmc, "trace")
    set_wpa_log_level("msgdump")

    zero_times = 0

    device = get_device(nmc, interface)

    while True:
        print("Sleeping 10 seconds...")

        try:
            time.sleep(10)
        except KeyboardInterrupt:
            break

        print_ap_info(device)

        count = get_access_point_count(device)

        if count == 0:
            print("No access points available")

            zero_times += 1
            if zero_times < 3:
                continue

            request_scan(device)

            print("Waiting for 10 seconds...")

            time.sleep(10)

            count = get_access_point_count(device)

            if count == 0:
                print("Scanning did NOT work")
            else:
                print("Scanning WORKED!!!")

            break
        else:
            zero_times = 0

    set_nm_log_level(nmc, "info")
    set_wpa_log_level("info")

    print("Exiting...")

if __name__ == "__main__":
    main()
