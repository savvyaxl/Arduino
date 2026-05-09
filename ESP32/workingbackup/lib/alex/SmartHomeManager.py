import uasyncio as asyncio
import json, ntptime, time, network, ssl
from machine import RTC, Pin
from microdot.microdot import Microdot
from mqtt_as import MQTTClient, config
from mysecrets import secrets
import globals as g
import ubinascii

# --- 1. WiFi Scanner Logic (Modified to not block) ---
def get_best_network():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    mac_raw = wlan.config('mac')
    mac_hex = ubinascii.hexlify(mac_raw, ':').decode()

    print("MAC Address:", mac_hex.replace(":", ""))
    scan_results = wlan.scan()
    for net in scan_results:
        ssid = net[0].decode()
        for secret in secrets:
            if ssid == secret['ssid']:
                return secret
    return None

def getTime():
    dt = rtc.datetime()
    return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"

# --- 2. Smart Home Manager ---
class SmartHomeManager:
    STORAGE_FILE = "alarms.json"
    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, utc_offset=-3):
        self.rtc = RTC()
        self.offset = utc_offset * 3600
        self.alarms = self._load_alarms()
        self.app = Microdot()
        self.mqtt = None
        self._setup_routes()

    def _load_alarms(self):
        try:
            with open(self.STORAGE_FILE, "r") as f:
                return json.load(f)
        except: return []

    def _save_alarms(self):
        with open(self.STORAGE_FILE, "w") as f:
            json.dump(self.alarms, f)

    async def sync_time(self):
        while True:
            try:
                ntptime.settime()
                t = time.time() + self.offset
                tm = time.localtime(t)
                self.rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
                print("NTP Sync Successful")
                await asyncio.sleep(86400) 
            except:
                print("NTP Sync Failed, retrying in 30s...")
                await asyncio.sleep(30)

    def getTime(self):
        dt = self.rtc.datetime()
        return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"
    
    async def _trigger_action(self, alarm):
        p = Pin(alarm['pin'], Pin.OUT)
        action = alarm.get('action', 'pulse')
        name = alarm.get('name', 'Alarm')
        
        # Hardware Action
        if action == "on": p.value(1)
        elif action == "off": p.value(0)
        elif action == "pulse":
            p.value(1)
            await asyncio.sleep(int(alarm['duration']))
            p.value(0)

        # MQTT Action
        if self.mqtt:
            msg = json.dumps({"event": "alarm_triggered", "name": name, "action": action})
            await self.mqtt.publish("home/alarms/events", msg, qos=1)

    async def alarm_checker_loop(self):
        while True:
            now = self.rtc.datetime()
            wd, h, m = now[3], now[4], now[5]
            for al in self.alarms:
                al_h, al_m = al['time'][0], al['time'][1]
                if wd in al['days'] and h == al_h and m == al_m:
                    if not al.get('triggered_today', False):
                        al['triggered_today'] = True
                        asyncio.create_task(self._trigger_action(al))
                elif m != al_m:
                    al['triggered_today'] = False
            await asyncio.sleep(10) # 10s check is plenty for minute-based alarms

    def _setup_routes(self):
        @self.app.route('/')
        async def index(request):
            now = self.rtc.datetime()
            current_time_str = f"{now[0]}-{now[1]:02d}-{now[2]:02d} {now[4]:02d}:{now[5]:02d}:{now[6]:02d}"
            current_day = self.DAY_NAMES[now[3]]

            rows = ""
            for i, a in enumerate(self.alarms):
                days_str = ", ".join([self.DAY_NAMES[d] for d in a['days']])
                action_label = a.get('action', 'pulse').upper()
                dur_info = f" | {a['duration']}s" if action_label == "PULSE" else ""
                name = a.get('name', 'Alarm')
                
                rows += f"<li><strong>{name}</strong><br>{a['time'][0]:02d}:{a['time'][1]:02d} | {days_str} | Pin:{a['pin']} | {action_label}{dur_info} <a class='del' href='/del?id={i}'>Delete</a></li>"
            
            day_boxes = "".join([f'<label><input type="checkbox" name="days" value="{i}" class="day-check" checked> {name}</label> ' for i, name in enumerate(self.DAY_NAMES)])

            html = f"""
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 20px; }}
                    .time-display {{ background: #333; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; border: 1px solid #03dac6; }}
                    .time-display h3 {{ margin: 0; color: #03dac6; }}
                    ul {{ list-style: none; padding: 0; }}
                    li {{ background: #1e1e1e; padding: 10px; margin-bottom: 15px; border-radius: 5px; border: 1px solid #333; line-height: 1.6; }}
                    input, select {{ background: #2c2c2c; color: white; border: 1px solid #444; padding: 8px; border-radius: 4px; width: 100%; margin: 5px 0; box-sizing: border-box; }}
                    input[type="checkbox"] {{ width: auto; }}
                    .btn {{ background: #03dac6; color: black; border: none; padding: 12px; width: 100%; font-weight: bold; cursor: pointer; border-radius: 4px; margin-top: 10px; }}
                    .del {{ color: #cf6679; text-decoration: none; float: right; font-weight: bold; }}
                    hr {{ border: 0; border-top: 1px solid #333; margin: 20px 0; }}
                </style>
                <script>
                    function toggleDays(source) {{
                        checkboxes = document.getElementsByClassName('day-check');
                        for(var i=0; i<checkboxes.length; i++) checkboxes[i].checked = source.checked;
                    }}
                </script>
            </head>
            <body>
                <div class="time-display">
                    <h3>{current_day} {current_time_str}</h3>
                    <small><a href="/" style="color:#03dac6; text-decoration:none;">↻ Refresh Time</a></small>
                </div>

                <h2>Active Alarms</h2>
                <ul>{rows if rows else "<li>No alarms set</li>"}</ul>
                <hr>
                <form action="/add">
                    Alarm Name: <input type="text" name="n" value="Alarm">
                    Time: <input type="time" name="t" required>
                    Pin: <input type="number" name="p" value="2">
                    Action: <select name="a">
                        <option value="pulse">Pulse (Timed)</option>
                        <option value="on">Permanent ON</option>
                        <option value="off">Permanent OFF</option>
                    </select>
                    Pulse Dur (sec): <input type="number" name="d" value="40">
                    <div style="margin: 15px 0;">
                        <strong>Schedule:</strong><br>
                        <label><input type="checkbox" onClick="toggleDays(this)" checked> Select All</label><br>
                        {day_boxes}
                    </div>
                    <input type="submit" class="btn" value="Save Alarm">
                </form>
            </body>
            </html>
            """
            return html, 200, {'Content-Type': 'text/html'}

    async def run(self):
        # 1. Find Network
        net = get_best_network()
        
        if not net:
            print("No known WiFi found!")
            return
        
        print(net)
        
        # 2. Setup SSL & MQTT Config
        # Assuming your SSLContext class is in ssl_helper.py
        import ssl # type: ignore
        #print(ssl.__file__)
        my_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        my_ssl.verify_mode = ssl.CERT_REQUIRED
        my_ssl.load_cert_chain("client.der", "client.key.der")
        my_ssl.load_verify_locations("CA.der")
        my_ssl.check_hostname = False 
        
        print(my_ssl)
        
        
        
        config['ssid'] = net['ssid']
        config['wifi_pw'] = net['password']
        config['server'] = net['broker']
        #config['server_hostname'] = net['broker']
        config['port'] = net['port']
        config['user'] = net['user']
        config['password'] = net['pass']
        config['ssl'] = my_ssl # Use the internal MicroPython TLS object
        
        print(config)
        # 3. Start MQTT
        self.mqtt = MQTTClient(config)
        print(self.mqtt)
        print(self.getTime())
        
        await self.mqtt.connect()
        
        # 4. Launch Background Tasks
        
        asyncio.create_task(self.alarm_checker_loop())
        
        print(f"System Ready. IP: {network.WLAN(network.STA_IF).ifconfig()[0]}")
        await self.app.start_server(port=80)

# --- 3. Entry Point ---
if __name__ == "__main__":
    manager = SmartHomeManager()
    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        pass
