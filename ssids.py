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
    print("Device path:", device)

    if device is None:
        sys.exit("Interface not found: {}".format(interface))

    return device

def get_access_point_count(device):
    count = len(device.get_access_points())

    print("Access point count:", count)

    return count

def request_scan(device):
    device.request_scan()

    print("WiFi scan requested")

def main():
    interface = get_interface()

    nmc = NM.Client.new(None)

    set_nm_log_level(nmc, "trace")
    set_wpa_log_level("msgdump")

    zero_times = 0

    device = get_device(nmc, interface)

    while True:
        print("Sleeping 5 seconds...")

        try:
            time.sleep(5)
        except KeyboardInterrupt:
            break

        count = get_access_point_count(device)
        count = 0

        if count == 0:
            print("No access points available")

            zero_times += 1
            if zero_times < 3:
                continue

            request_scan(device)

            print("Waiting for 10 seconds...")

            time.sleep(10)

            count = get_access_point_count(device)
            count = 0

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
