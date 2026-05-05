import uasyncio as asyncio
import json, ntptime, time, os
from machine import RTC, Pin
from microdot.microdot import Microdot # Using your specific import

class SmartHomeManager:
    STORAGE_FILE = "alarms.json"
    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

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
        while True:
            try:
                ntptime.settime()
                t = time.time() + self.offset
                tm = time.localtime(t)
                # ESP32 RTC: (y, m, d, wd, h, m, s, ss)
                self.rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
                print("NTP Sync Successful")
                await asyncio.sleep(86400) 
            except:
                await asyncio.sleep(30)

    async def _trigger_action(self, alarm):
        p = Pin(alarm['pin'], Pin.OUT)
        action = alarm.get('action', 'pulse')
        name = alarm.get('name', 'Unnamed Alarm')
        t = alarm['time']
        
        # The print statement you requested
        print(f"ALARM TRIGGERED: {name} at {t[0]:02d}:{t[1]:02d}")
        if action == "on": p.value(1)
        elif action == "off": p.value(0)
        elif action == "pulse":
            p.value(1)
            await asyncio.sleep(int(alarm['duration']))
            p.value(0)

    async def alarm_checker_loop(self):
        while True:
            now = self.rtc.datetime()
            wd, h, m, s = now[3], now[4], now[5], now[6]
            for al in self.alarms:
                al_h, al_m, al_s = al['time']
                if wd in al['days'] and h == al_h and m == al_m and s == al_s:
                    if not al.get('triggered_today', False):
                        al['triggered_today'] = True
                        asyncio.create_task(self._trigger_action(al))
                        print(f"Alarm triggered for Pin {al['pin']} at {h:02d}:{m:02d}:{s:02d}")
                if m != al_m and al.get('triggered_today', False):
                    al['triggered_today'] = False
            await asyncio.sleep(0.8)

    def _setup_routes(self):
        @self.app.route('/')
        async def index(request):
            # Get Current RTC Time
            now = self.rtc.datetime()
            # Format: YYYY-MM-DD HH:MM:SS
            current_time_str = f"{now[0]}-{now[1]:02d}-{now[2]:02d} {now[4]:02d}:{now[5]:02d}:{now[6]:02d}"
            # Get Day of Week Name
            current_day = self.DAY_NAMES[now[3]]

            rows = ""
            for i, a in enumerate(self.alarms):
                days_str = ", ".join([self.DAY_NAMES[d] for d in a['days']])
                action_label = a.get('action', 'pulse').upper()
                dur_info = f" | {a['duration']}s" if action_label == "PULSE" else ""
                
                rows += f"<li>{a['time'][0]:02d}:{a['time'][1]:02d} | {days_str} | Pin:{a['pin']} | {action_label}{dur_info} <a class='del' href='/del?id={i}'>Delete</a></li>"
            
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
                    li {{ background: #1e1e1e; padding: 10px; margin-bottom: 10px; border-radius: 5px; border: 1px solid #333; }}
                    input, select {{ background: #2c2c2c; color: white; border: 1px solid #444; padding: 8px; border-radius: 4px; width: 100%; margin: 5px 0; }}
                    input[type="checkbox"] {{ width: auto; }}
                    .btn {{ background: #03dac6; color: black; border: none; padding: 10px; width: 100%; font-weight: bold; cursor: pointer; border-radius: 4px; }}
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

                <h2>Alarms</h2>
                <ul>{rows if rows else "<li>No alarms set</li>"}</ul>
                <hr>
                <form action="/add">
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

        @self.app.route('/add')
        async def add(request):
            t_parts = request.args.get('t').split(':')
            days_raw = request.args.getlist('days')
            selected_days = [int(d) for d in days_raw] if days_raw else list(range(7))
            self.alarms.append({
                "time": [int(t_parts[0]), int(t_parts[1]), 0],
                "days": selected_days,
                "action": request.args.get('a'),
                "duration": int(float(request.args.get('d', 0))),
                "pin": int(request.args.get('p')),
                "triggered_today": False
            })
            self._save_alarms()
            return "", 302, {'Location': '/'}

        @self.app.route('/del')
        async def delete(request):
            idx = int(request.args.get('id'))
            if 0 <= idx < len(self.alarms):
                self.alarms.pop(idx)
                self._save_alarms()
            return "", 302, {'Location': '/'}

    async def run(self):
        asyncio.create_task(self.sync_time())
        asyncio.create_task(self.alarm_checker_loop())
        print("Server running on port 80...")
        await self.app.start_server(port=80)
