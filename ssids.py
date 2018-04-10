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

def set_wpa_log_level(bus, level):
    proxy = bus.get_object("fi.w1.wpa_supplicant1", "/fi/w1/wpa_supplicant1")
    properties = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")

    if level == "msgdump":
        properties.Set("fi.w1.wpa_supplicant1", "DebugTimestamp", True)

    properties.Set("fi.w1.wpa_supplicant1", "DebugLevel", level)

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

def send_logs():
    print("Pulling and sending logs")

    os.chdir("/tmp/")

    os.system("journalctl -b  -u NetworkManager -u wpa_supplicant > network-logs.txt")

    os.system("tar -czf network-logs.tar.gz network-logs.txt")

    location = os.popen('curl -s -H "Max-Days: 7" --upload-file ./network-logs.tar.gz https://transfer.sh/network-logs.tar.gz').read()

    os.remove("network-logs.txt")

    os.remove("network-logs.tar.gz")

    print(location)


def main():
    interface = get_interface()

    bus = dbus.SystemBus()

    set_nm_log_level(bus, "debug")
    set_wpa_log_level(bus, "msgdump")

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

                send_logs()

                break
            else:
                print("Scanning WORKED!!!")

        print("Sleeping 30 seconds...")
        time.sleep(30)

    set_nm_log_level(bus, "info")
    set_wpa_log_level(bus, "info")

    print("Exiting...")

if __name__ == "__main__":
    main()
