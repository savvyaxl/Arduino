import uasyncio as asyncio
import json, ntptime, time, os
from machine import RTC, Pin
from microdot.microdot import Microdot

class SmartHomeManager:
    STORAGE_FILE = "alarms.json"

    def __init__(self, utc_offset=-5):
        self.rtc = RTC()
        self.offset = utc_offset * 3600
        self.alarms = self._load_alarms()
        self.app = Microdot()
        self._setup_routes()

    def _load_alarms(self):
        try:
            with open(self.STORAGE_FILE, "r") as f:
                return json.load(f)
        except:
            return []

    def _save_alarms(self):
        with open(self.STORAGE_FILE, "w") as f:
            json.dump(self.alarms, f)

    async def sync_time(self):
        """Periodically syncs RTC with NTP time."""
        while True:
            try:
                print("Syncing time with NTP...")
                ntptime.settime()
                t = time.time() + self.offset
                tm = time.localtime(t)
                # ESP32 RTC: (year, month, day, weekday, hours, minutes, seconds, subseconds)
                self.rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
                print("NTP Sync Successful")
                await asyncio.sleep(86400) 
            except Exception as e:
                print("NTP Sync Failed:", e)
                await asyncio.sleep(30)

    async def _trigger_action(self, alarm):
        """Handles the actual hardware interaction."""
        p = Pin(alarm['pin'], Pin.OUT)
        action = alarm.get('action', 'pulse')
        
        if action == "on":
            p.value(1)
            print(f"Pin {alarm['pin']} -> Permanent ON")
        elif action == "off":
            p.value(0)
            print(f"Pin {alarm['pin']} -> Permanent OFF")
        elif action == "pulse":
            p.value(1)
            # Duration is treated as a whole integer
            await asyncio.sleep(int(alarm['duration']))
            p.value(0)
            print(f"Pin {alarm['pin']} -> Pulsed for {alarm['duration']}s")

    async def alarm_checker_loop(self):
        """Background loop to check for triggered alarms."""
        while True:
            now = self.rtc.datetime()
            # Indexing: 3=weekday, 4=hour, 5=minute, 6=second
            wd, h, m, s = now[3], now[4], now[5], now[6]
            
            for al in self.alarms:
                al_h, al_m, al_s = al['time']
                
                if wd in al['days'] and h == al_h and m == al_m and s == al_s:
                    if not al.get('triggered_today', False):
                        al['triggered_today'] = True
                        asyncio.create_task(self._trigger_action(al))
                
                # Reset flag once the specific alarm minute has passed
                if m != al_m and al.get('triggered_today', False):
                    al['triggered_today'] = False
            
            await asyncio.sleep(0.8)

    def _setup_routes(self):
        @self.app.route('/')
        async def index(request):
            rows = ""
            for i, a in enumerate(self.alarms):
                action_label = a.get('action', 'pulse').upper()
                rows += f"<li>{a['time'][0]:02d}:{a['time'][1]:02d} | Pin:{a['pin']} | {action_label} ({a['duration']}s) <a href='/del?id={i}'>[Delete]</a></li>"
            
            html = f"""
            <html>
            <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
            <body>
                <h1>ESP32 Alarm Manager</h1>
                <ul>{rows if rows else "<li>No alarms set</li>"}</ul>
                <hr>
                <form action="/add">
                    Time: <input type="time" name="t" required><br><br>
                    Pin: <input type="number" name="p" value="2"><br><br>
                    Action: 
                    <select name="a">
                        <option value="pulse">Pulse (Timed)</option>
                        <option value="on">Permanent ON</option>
                        <option value="off">Permanent OFF</option>
                    </select><br><br>
                    Pulse Dur (Whole Seconds): <input type="number" name="d" value="40"><br><br>
                    <input type="submit" value="Add Alarm">
                </form>
            </body>
            </html>
            """
            return html, 200, {'Content-Type': 'text/html'}

        @self.app.route('/add')
        async def add(request):
            try:
                t_parts = request.args.get('t').split(':')
                # Explicitly cast duration to int to ensure only whole seconds are stored
                dur = int(float(request.args.get('d', 0)))
                
                new_alarm = {
                    "time": [int(t_parts[0]), int(t_parts[1]), 0],
                    "action": request.args.get('a'),
                    "duration": dur,
                    "pin": int(request.args.get('p')),
                    "days": [0,1,2,3,4,5,6],
                    "triggered_today": False
                }
                self.alarms.append(new_alarm)
                self._save_alarms()
                # Redirect back to home page immediately
                return "", 302, {'Location': '/'}
            except Exception as e:
                return f"Error: {e}", 400
            
        @self.app.route('/del')
        async def delete(request):
            idx = int(request.args.get('id'))
            if 0 <= idx < len(self.alarms):
                self.alarms.pop(idx)
                self._save_alarms()
            # Redirect back to home page immediately
            return "", 302, {'Location': '/'}

    async def run(self):
        asyncio.create_task(self.sync_time())
        asyncio.create_task(self.alarm_checker_loop())
        print("Web server starting...")
        await self.app.start_server(port=80)
