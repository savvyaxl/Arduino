import network # pyright: ignore[reportMissingImports]
from mysecrets import secrets
import globals as g
import time
import uasyncio as asyncio  # pyright: ignore[reportMissingImports]

class WiFiHandler:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        self.disconnect_wifi()
        self.scan_wifi()
        # Fast 3-second initial block on cold boot to quickly step into the main event loop
        self.connect_to_wifi_blocking(g.myssid, g.mypass)

    def scan_wifi(self):
        try:
            scan_results = self.wlan.scan()
        except Exception:
            return  # Prevent crashes if network chip interface is busy during a router reboot

        print("{:<30} {:<10} {:<8}".format("SSID", "Channel", "RSSI"))
        print("="*48)
        
        matched_secret = None
        for net in scan_results:
            try:
                ssid_bytes = net[0]
                if not ssid_bytes:
                    continue
                ssid = ssid_bytes.decode('utf-8')
                channel = net[2]
                rssi = net[3]
                print("{:<30} {:<10} {:<8}".format(ssid, channel, rssi))
                
                # Check for a matching credentials profile in secrets
                if not matched_secret:
                    for secret in secrets:
                        if ssid == secret['ssid']:
                            matched_secret = secret
            except Exception:
                continue
            
        if matched_secret:
            print("="*48)
            print(f"Target network profile selected: {matched_secret['ssid']}")
            g.myssid = matched_secret['ssid']
            g.mypass = matched_secret['password']
            g.broker = matched_secret['broker']
            g.mqport = matched_secret['port']
            g.mquser = matched_secret['user']
            g.mqpass = matched_secret['pass']

    def connect_to_wifi_blocking(self, ssid, password):
        """Initial boot step connection framework."""
        if not self.wlan.isconnected() and ssid:
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
        """Asynchronous execution pathway ensuring local alarms can fire uninterrupted."""
        if not self.wlan.isconnected() and ssid:
            try:
                self.wlan.disconnect()
                print(f"\nConnecting asynchronously to: {ssid}")
                self.wlan.connect(ssid, password)
            except Exception as e:
                print(f"Wi-Fi write error: {e}")
            
            # Non-blocking async loop keeps context execution moving cleanly
            timeout = 15
            while not self.wlan.isconnected() and timeout > 0:
                print('.', end='')
                await asyncio.sleep(1)  # <-- Yields execution control back to alarm loop
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
            try:
                self.wlan.disconnect()
                print("Disconnected from Wi-Fi.")
            except Exception:
                pass

    async def reconnect_wifi_async(self):
        """Non-blocking background pipeline tailored for unexpected router reboots."""
        self.disconnect_wifi()
        await asyncio.sleep(1)
        self.scan_wifi()
        await self.connect_to_wifi_async(g.myssid, g.mypass)
