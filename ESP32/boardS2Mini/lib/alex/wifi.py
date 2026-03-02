import network
from mysecrets import secrets
import globals as g
import time

# Get the Wi-Fi station interface object
wlan = network.WLAN(network.STA_IF)

# Activate the interface to enable Wi-Fi
wlan.active(True)


def scan_wifi():
    # Perform the scan
    scan_results = wlan.scan()

    # Decode and print the results
    # print("Found %d networks:" % len(scan_results))
    print("{:<30} {:<10} {:<8}".format("SSID", "Channel", "RSSI"))
    print("="*48)
    for net in scan_results:
        ssid = net[0].decode()
        channel = net[2]
        rssi = net[3]
        print("{:<30} {:<10} {:<8}".format(ssid, channel, rssi))
        
    doBreak = False
    for net in scan_results:
        ssid = net[0].decode()
        channel = net[2]
        rssi = net[3]
        
        if doBreak:
            break
        for secret in secrets:
            if ssid == secret['ssid']:
                print("="*48)
                print("{:<30} {:<10} {:<8}".format(ssid, channel, rssi))
                g.myssid = secret['ssid']
                g.mypass = secret['password']
                g.broker = secret['broker']
                g.mqport = secret['port']
                g.mquser = secret['user']
                g.mqpass = secret['pass']
                doBreak = True

def connect_to_wifi(ssid, password):
    if not wlan.isconnected():
        print("Connecting to network...")
        wlan.connect(ssid, password)
        # Wait for the connection to be established
        timeout = 10  # 10-second timeout
        while not wlan.isconnected() and timeout > 0:
            print('.', end='')
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():
        g.mac = ''.join(['%02x' % b for b in wlan.config('mac')])
        g.ip = wlan.ifconfig()[0]
        print('\nConnected!')
        print('Network IP Address:', g.ip, 'mac: ', g.mac)
    else:
        print('\nConnection failed.')

# Connect to the Wi-Fi network
scan_wifi()
connect_to_wifi(g.myssid, g.mypass)