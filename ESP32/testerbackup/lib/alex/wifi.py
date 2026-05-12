import network
from mysecrets import secrets
import globals as g
import time


class WiFiHandler:
    def __init__(self):
        self.ssid = None
        self.channel = None
        self.rssi = None
        self.wlan = network.WLAN(network.STA_IF)

        # Activate the interface to enable Wi-Fi
        self.wlan.active(True)
        self.disconnect_wifi()
        if self.wlan.isconnected():
            g.mac = ''.join(['%02x' % b for b in self.wlan.config('mac')])
            g.ip = self.wlan.ifconfig()[0]
            print('Already connected!')
            print('Network IP Address:', g.ip, 'mac: ', g.mac)
        else:
            print('Not connected to Wi-Fi. Please call connect_to_wifi(ssid, password) to connect.')
            self.scan_wifi()
            self.connect_to_wifi(g.myssid, g.mypass)


    def scan_wifi(self):
        # Perform the scan
        scan_results = self.wlan.scan()

        # Decode and print the results
        # print("Found %d networks:" % len(scan_results))
        print("{:<30} {:<10} {:<8}".format("SSID", "Channel", "RSSI"))
        print("="*48)
        for net in scan_results:
            self.ssid = net[0].decode()
            self.channel = net[2]
            self.rssi = net[3]
            print("{:<30} {:<10} {:<8}".format(self.ssid, self.channel, self.rssi))
            
        doBreak = False
        for net in scan_results:
            if doBreak:
                break
            
            self.ssid = net[0].decode()
            self.channel = net[2]
            self.rssi = net[3]
            
            for secret in secrets:
                if self.ssid == secret['ssid']:
                    print("="*48)
                    print("{:<30} {:<10} {:<8}".format(self.ssid, self.channel, self.rssi))
                    g.myssid = secret['ssid']
                    g.mypass = secret['password']
                    g.broker = secret['broker']
                    g.mqport = secret['port']
                    g.mquser = secret['user']
                    g.mqpass = secret['pass']
                    doBreak = True

    def connect_to_wifi(self,ssid, password):
        if not self.wlan.isconnected():
            print("Connecting to network..." , "{:<30}".format(self.ssid))
            self.wlan.connect(ssid, password)
            # Wait for the connection to be established
            timeout = 10  # 10-second timeout
            while not self.wlan.isconnected() and timeout > 0:
                print('.', end='')
                time.sleep(1)
                timeout -= 1

        if self.wlan.isconnected():
            g.mac = ''.join(['%02x' % b for b in self.wlan.config('mac')])
            g.ip = self.wlan.ifconfig()[0]
            print('\nConnected!')
            print('Network IP Address:', g.ip, 'mac: ', g.mac)
        else:
            print('\nConnection failed.')

    def disconnect_wifi(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
            print("Disconnected from Wi-Fi.")
        else:
            print("Not connected to any Wi-Fi network.")

    def reconnect_wifi(self):
        self.disconnect_wifi()
        self.scan_wifi()
        self.connect_to_wifi(g.myssid, g.mypass)
