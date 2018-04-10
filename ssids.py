#!/usr/bin/env python
import sys
import time
import os

import dbus

def set_nm_log_level(bus, level):
    proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
    nm = dbus.Interface(proxy, "org.freedesktop.NetworkManager")
    nm.SetLogging(level, "")

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

def get_device(bus, interface):
    proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
    nm = dbus.Interface(proxy, "org.freedesktop.NetworkManager")
    device = nm.GetDeviceByIpIface(interface)

    print("Device path:", device)

    return device

def get_access_point_count(bus, device):
    proxy = bus.get_object("org.freedesktop.NetworkManager", device)
    wireless = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Device.Wireless")
    count = len(wireless.GetAllAccessPoints())

    print("Access point count:", count)

    return count

def request_scan(bus, device):
    proxy = bus.get_object("org.freedesktop.NetworkManager", device)
    wireless = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Device.Wireless")
    wireless.RequestScan([])

    print("WiFi scan requested")

def main():
    interface = get_interface()

    bus = dbus.SystemBus()

    set_nm_log_level(bus, "debug")
    set_wpa_log_level("msgdump")

    while True:
        device = get_device(bus, interface)
        count = get_access_point_count(bus, device)

        if count == 0:
            print("No access points available")

            request_scan(bus, device)

            print("Waiting for 10 seconds...")

            time.sleep(10)

            count = get_access_point_count(bus, device)

            if count == 0:
                print("Scanning did NOT work")
            else:
                print("Scanning WORKED!!!")

            break

        print("Sleeping 30 seconds...")
        time.sleep(30)

    set_nm_log_level(bus, "info")
    set_wpa_log_level("info")

    print("Exiting...")

if __name__ == "__main__":
    main()
