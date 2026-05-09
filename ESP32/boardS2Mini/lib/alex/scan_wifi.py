import network # pyright: ignore[reportMissingImports]
from mysecrets import secrets
import globals as g

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

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
    
    for secret in secrets:
        if ssid == secret['ssid']:
            print("="*48)
            # print("{:<30} {:<10} {:<8}".format(self.ssid, self.channel, self.rssi))
            g.myssid = secret['ssid']
            g.mypass = secret['password']
            g.broker = secret['broker']
            g.mqport = secret['port']
            g.mquser = secret['user']
            g.mqpass = secret['pass']
            doBreak = True
