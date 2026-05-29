from capacity_tester import BatteryTester # Assuming your class is in this file
import wifi_as as WiFi
import uasyncio as asyncio # type: ignore
import json, ntptime, time, ds1302 # type: ignore
from machine import RTC, Pin # type: ignore
from microdot.microdot import Microdot
import gc, network # type: ignore
from mysecrets import secrets
import mqtt as MQTT
import globals as g






class SmartHomeManager:
    STORAGE_FILE = "alarms.json"
    PINDEF_FILE = "pin_definitions.json"
    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, utc_offset=-3):
        self.rtc = RTC()
        self.offset = utc_offset * 3600
        self.app = Microdot()
        self._setup_routes()
        self.mqtt = MQTT.MQTTHandler()
        self.subscribed = False
        self.subscribe_topic = None


    def _setup_routes(self):
        @self.app.route('/get-time')
        async def get_time(request):
            now = self.rtc.datetime()
            current_time_str = f"{now[0]}-{now[1]:02d}-{now[2]:02d} {now[4]:02d}:{now[5]:02d}:{now[6]:02d}"
            current_day = self.DAY_NAMES[now[3]]
            return f"{current_day} {current_time_str}", 200, {'Content-Type': 'text/plain; charset=utf-8'}

        @self.app.route('/')
        async def index(request):
            now = self.rtc.datetime()
            current_time_str = f"{now[0]}-{now[1]:02d}-{now[2]:02d} {now[4]:02d}:{now[5]:02d}:{now[6]:02d}"
            current_day = self.DAY_NAMES[now[3]]
            sorted_alarms = sorted(self.alarms, key=lambda x: (int(x['time'][0]), int(x['time'][1])))

            rows = ""
            for i, a in enumerate(sorted_alarms):
                days_str = ", ".join([self.DAY_NAMES[d] for d in a['days']])
                action_label = a.get('action', 'pulse').upper()
                dur_info = f" | {a['duration']}s" if action_label == "PULSE" else ""
                name = a.get('name', 'Alarm')
                
                rows += f"<li><strong>{name}</strong><br>{a['time'][0]:02d}:{a['time'][1]:02d} | {days_str} | Pin:{a['pin']} | {action_label}{dur_info} <a class='del' href='/del?id={i}'>Delete</a></li>"
            
            day_boxes = "".join([f'<label><input type="checkbox" name="days" value="{i}" class="day-check" checked> {name}</label> ' for i, name in enumerate(self.DAY_NAMES)])
            pin_options = "".join([f'<option value="{name[0]}">{name[0]}</option>' 
                            for name in self.allowed_pins.items()])

            html = f"""
            <html>
            <head>
                <meta charset="UTF-8">
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
                    .refresh-controls {{ margin-top: 8px; font-size: 14px; color: #aaa; }}
                    .refresh-controls button {{ background: none; border: none; color: #03dac6; cursor: pointer; font-size: 14px; text-decoration: underline; padding: 0; }}
                </style>
                <script>
                    function toggleDays(source) {{
                        var checkboxes = document.getElementsByClassName('day-check');
                        for(var i=0; i<checkboxes.length; i++) checkboxes[i].checked = source.checked;
                    }}
                    
                    function updateAlarmName(selectEl) {{
                        var nameInput = document.getElementById('alarm-name');
                        if (selectEl.selectedIndex >= 0) {{
                            nameInput.value = selectEl.options[selectEl.selectedIndex].text;
                        }}
                    }}
                    
                    // --- Auto-Refresh Application Logic ---
                    let timerInstance = null;

                    async function fetchLiveTime() {{
                        try {{
                            let res = await fetch('/get-time');
                            if (res.ok) {{
                                let txt = await res.text();
                                document.getElementById('live-clock').innerText = txt;
                            }}
                        }} catch (err) {{
                            console.log("Clock sync failure", err);
                        }}
                    }}

                    function manageAutoRefresh() {{
                        const checkbox = document.getElementById('auto-refresh-toggle');
                        if (checkbox.checked) {{
                            if (!timerInstance) {{
                                timerInstance = setInterval(fetchLiveTime, 1000);
                            }}
                        }} else {{
                            clearInterval(timerInstance);
                            timerInstance = null;
                        }}
                    }}
                    
                    window.addEventListener('DOMContentLoaded', function() {{
                        var devSelect = document.getElementById('dev-select');
                        if (devSelect) updateAlarmName(devSelect);
                        
                        // Initialize auto-refresh when the DOM finishes rendering
                        manageAutoRefresh();
                    }});
                </script>
            </head>
            <body>
                <div class="time-display">
                    <!-- Added distinct targeting ID here -->
                    <h3 id="live-clock">{current_day} {current_time_str}</h3>
                    
                    <div class="refresh-controls">
                        <button onclick="fetchLiveTime()">↻ Refresh Time</button>
                        <span style="margin: 0 10px;">|</span>
                        <label>
                            <input type="checkbox" id="auto-refresh-toggle" checked onchange="manageAutoRefresh()"> Auto-Refresh (1s)
                        </label>
                    </div>
                </div>

                <h2>Active Alarms</h2>
                <ul>{rows if rows else "<li>No alarms set</li>"}</ul>
                <hr>
                <form action="/add">
                    Alarm Name: <input type="text" name="n" id="alarm-name" value="Alarm">
                    Time: <input type="time" name="t" required>
                    Device: <select name="pn" id="dev-select" onchange="updateAlarmName(this)">
                        {pin_options}
                    </select>
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
                    <a href="/config" class="btn">Config</a>
                </form>
            </body>
            </html>
            """
            return html, 200, {'Content-Type': 'text/html; charset=utf-8'}









try:
    ntptime.settime()
    print("Time synchronized!")
    print(f"{g.format_time(time.localtime(time.time() - 3 * 3600))}")
except:
    print("Failed to sync time")

sensor_name="Battery"
sensor_data=["Current", "Voltage", "Energy"]
#sensor = SensorManager(sensor_name, sensor_data)

mqtt = MQTT.MQTTHandler(sensor_name, sensor_data)
mqtt.connect()
mqtt.publish_config("bob","sam")

tester = BatteryTester(adc_pin_num=5, mosfet_pin_num=33, r_load=35.3)



# Use a loop to catch every JSON update yielded by the generator
for mqtt_json in tester.run_test_mqtt(cutoff_v=3.0, interval=10):
    # 'client' would be your Umqtt.simple instance
    try:
        mqtt.publish(mqtt_json)
    except Exception as e:
        print(f"Failed to publish MQTT message: {e}")
        if not WiFi.wlan.isconnected():
            WiFi.reconnect_wifi()
            try:
                mqtt.check_msg()
            except Exception as e:
                mqtt.connect()  # Reconnect MQTT if needed
                mqtt.publish_config()

# 1. SETUP
# Use the pins from the diagram: ADC=34, MOSFET=32
# Use your measured resistance: 35.3 ohms
#tester = BatteryTester(adc_pin_num=4, mosfet_pin_num=33, r_load=35.3)
#tester.read_voltage(maxcount=30, interval=1)
#tester.run_test(cutoff_v=3.0, interval=1)
