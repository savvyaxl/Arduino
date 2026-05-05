import uasyncio as asyncio
import json, ntptime, time, os
from machine import RTC, Pin
from microdot.microdot import Microdot

class SmartHomeManager:
    STORAGE_FILE = "alarms.json"
    # Mapping for display
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
                # ESP32 RTC: (year, month, day, weekday, hours, minutes, seconds, subseconds)
                # weekday 0-6 for Mon-Sun
                self.rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
                print("NTP Sync Successful")
                await asyncio.sleep(86400) 
            except:
                await asyncio.sleep(30)

    async def _trigger_action(self, alarm):
        p = Pin(alarm['pin'], Pin.OUT)
        action = alarm.get('action', 'pulse')
        if action == "on": p.value(1)
        elif action == "off": p.value(0)
        elif action == "pulse":
            p.value(1)
            await asyncio.sleep(int(alarm['duration']))
            p.value(0)

    async def alarm_checker_loop(self):
        while True:
            now = self.rtc.datetime()
            # Index 3 is weekday (0=Mon, 6=Sun) on ESP32
            wd, h, m, s = now[3], now[4], now[5], now[6]
            
            for al in self.alarms:
                al_h, al_m, al_s = al['time']
                if wd in al['days'] and h == al_h and m == al_m and s == al_s:
                    if not al.get('triggered_today', False):
                        al['triggered_today'] = True
                        asyncio.create_task(self._trigger_action(al))
                
                if m != al_m and al.get('triggered_today', False):
                    al['triggered_today'] = False
            
            await asyncio.sleep(0.8)

    def _setup_routes(self):
        @self.app.route('/')
        async def index(request):
            rows = ""
            for i, a in enumerate(self.alarms):
                days_str = ", ".join([self.DAY_NAMES[d] for d in a['days']])
                action_label = a.get('action', 'pulse').upper()
                rows += f"<li>{a['time']:02d}:{a['time']:02d} | {days_str} | Pin:{a['pin']} | {action_label} ({a['duration']}s) <a href='/del?id={i}'>[Delete]</a></li>"
            
            day_boxes = ""
            for i, name in enumerate(self.DAY_NAMES):
                day_boxes += f'<input type="checkbox" name="days" value="{i}" class="day-check" checked> {name} '

            html = f"""
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <script>
                    function toggleDays(source) {{
                        checkboxes = document.getElementsByClassName('day-check');
                        for(var i in checkboxes) checkboxes[i].checked = source.checked;
                    }}
                </script>
            </head>
            <body>
                <h1>ESP32 Alarm Manager</h1>
                <ul>{rows if rows else "<li>No alarms set</li>"}</ul>
                <hr>
                <form action="/add">
                    Time: <input type="time" name="t" required><br><br>
                    
                    <strong>Days:</strong><br>
                    <input type="checkbox" onClick="toggleDays(this)" checked> <em>Select/Deselect All</em><br>
                    {day_boxes}<br><br>
                    
                    Pin: <input type="number" name="p" value="2"><br><br>
                    Action: 
                    <select name="a">
                        <option value="pulse">Pulse (Timed)</option>
                        <option value="on">Permanent ON</option>
                        <option value="off">Permanent OFF</option>
                    </select><br><br>
                    Pulse Dur (sec): <input type="number" name="d" value="40"><br><br>
                    <input type="submit" value="Add Alarm">
                </form>
            </body>
            </html>
            """
            return html, 200, {'Content-Type': 'text/html'}

        @self.app.route('/add')
        async def add(request):
            t_parts = request.args.get('t').split(':')
            days_raw = request.args.getlist('days')
            # If no days selected, we'll default to all days to avoid "ghost" alarms
            selected_days = [int(d) for d in days_raw] if days_raw else list(range(7))
            
            new_alarm = {
                "time": [int(t_parts[0]), int(t_parts[1]), 0],
                "days": selected_days,
                "action": request.args.get('a'),
                "duration": int(float(request.args.get('d', 0))),
                "pin": int(request.args.get('p')),
                "triggered_today": False
            }
            self.alarms.append(new_alarm)
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
        await self.app.start_server(port=80)
