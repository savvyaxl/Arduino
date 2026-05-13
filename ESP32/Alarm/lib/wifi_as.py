import network # pyright: ignore[reportMissingImports]
from mysecrets import secrets
import globals as g
import time
import uasyncio as asyncio  # pyright: ignore[reportMissingImports] Added for non-blocking recovery loops

class WiFiHandler:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        self.disconnect_wifi()
        self.scan_wifi()
        # Initial boot connection remains blocking intentionally to establish core state
        self.connect_to_wifi_blocking(g.myssid, g.mypass)

    def scan_wifi(self):
        try:
            scan_results = self.wlan.scan()
        except Exception:
            return  # Prevent crash if hardware driver is busy mid-reboot

        print("{:<30} {:<10} {:<8}".format("SSID", "Channel", "RSSI"))
        print("="*48)
        for net in scan_results:
            try:
                ssid = net[0].decode()
                channel = net[2]
                rssi = net[3]
                print("{:<30} {:<10} {:<8}".format(ssid, channel, rssi))
            except Exception:
                continue
            
        doBreak = False
        for net in scan_results:
            if doBreak:
                break            
            try:
                self.ssid = net[0].decode()
                for secret in secrets:
                    if self.ssid == secret['ssid']:
                        print("="*48)
                        g.myssid = secret['ssid']
                        g.mypass = secret['password']
                        g.broker = secret['broker']
                        g.mqport = secret['port']
                        g.mquser = secret['user']
                        g.mqpass = secret['pass']
                        doBreak = True
            except Exception:
                continue

    def connect_to_wifi_blocking(self, ssid, password):
        """Used strictly on initial cold boot setup."""
        if not self.wlan.isconnected():
            try:
                self.wlan.disconnect()
                self.wlan.connect(ssid, password)
            except Exception:
                pass
            timeout = 3
            while not self.wlan.isconnected() and timeout > 0:
                time.sleep(1)
                timeout -= 1
        self._verify_connection_state()

    async def connect_to_wifi_async(self, ssid, password):
        """Asynchronous connection implementation ensuring background alarms can fire."""
        if not self.wlan.isconnected():
            try:
                self.wlan.disconnect()
                print(f"Connecting asynchronously to: {ssid}")
                self.wlan.connect(ssid, password)
            except Exception as e:
                print(f"Wi-Fi write error: {e}")
            
            # Non-blocking 15-second loop allows alarms to breathe
            timeout = 15
            while not self.wlan.isconnected() and timeout > 0:
                print('.', end='')
                await asyncio.sleep(1)  # <-- Keeps alarms running safely
                timeout -= 1

        self._verify_connection_state()

    def _verify_connection_state(self):
        if self.wlan.isconnected():
            g.mac = ''.join(['%02x' % b for b in self.wlan.config('mac')])
            g.ip = self.wlan.ifconfig()[0]
            print('\nConnected Successfully!')
            print('Network IP Address:', g.ip, 'mac:', g.mac)
        else:
            print('\nConnection cycle failed.')

    def disconnect_wifi(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
            print("Disconnected from Wi-Fi.")

    async def reconnect_wifi_async(self):
        """Non-blocking execution pathway optimized for router reboots."""
        self.disconnect_wifi()
        await asyncio.sleep(1)
        self.scan_wifi()
        await self.connect_to_wifi_async(g.myssid, g.mypass)
