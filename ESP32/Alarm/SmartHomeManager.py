import uasyncio as asyncio # type: ignore
import json, ntptime, time, ds1302 # type: ignore
from machine import RTC, Pin, SoftI2C # type: ignore
from microdot.microdot import Microdot
import gc, network # type: ignore
# from mysecrets import secrets
import mqtt as MQTT
import wifi_as as WIFI
import globals as g
from writer import Writer

class SmartHomeManager:
    STORAGE_FILE = "alarms.json"
    PINDEF_FILE = "pin_definitions.json"
    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, utc_offset=-3, dhtPin=None, owPin=None, scl=Pin(7), sda=Pin(9)):
        self.rtc = RTC()
        self.offset = utc_offset * 3600
        self.alarms = self._load_alarms()
        self.allowed_pins = self._load_pin_definitions()
        self.app = Microdot()
        self._setup_routes()
        self.mqtt = MQTT.MQTTHandler()
        self.subscribed = False
        self.subscribe_topic = None

        self.dht_sensor = None
        self.temp = None
        self.hum = None
        if dhtPin is not None:
            import dht # type: ignore
            self.dht_sensor = dht.DHT11(Pin(dhtPin))  # Initialize DHT11 sensor on specified GPIO

        self.ds_sensor = None
        self.roms = []
        self.temp_c = None
        if owPin is not None:
            import ds18x20 # type: ignore
            import onewire # type: ignore
            ow = onewire.OneWire(Pin(owPin))  # Initialize OneWire on specified GPIO
            self.ds_sensor = ds18x20.DS18X20(ow)
            print("MQTT DS18X20 Sender Task started...")
            print("Scanning for 1-Wire devices...")
            try:
                self.roms = self.ds_sensor.scan()
                print(f"Found {len(self.roms)} Dallas temperature sensor(s).")
            except Exception as e:
                print(f"Initial scan failed: {e}")
                self.roms = []

        if scl is not None and sda is not None:
            import ssd1306  # type: ignore
            #import freesans20
            import courier20

            i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda))
            width = 128
            height = 64
            self.oled = ssd1306.SSD1306_I2C(width, height, i2c)
            self.w = Writer(self.oled, courier20)
            self.CALIBRATION_MAP = {
                "2894816b00000071": (0.0, 0.0), #(0.98172, -0.16892), 
            }

    async def write_ds18x20_to_oled(self, text, line=0):
        Writer.set_textpos(self.oled, line * 20, 0)
        #self.w.printstring(f"012345678 {temp:.2f} 012345678")
        self.w.printstring(f"{text}")
        self.oled.show()

    def getTime(self):
        dt = self.rtc.datetime()
        return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"

    def _load_alarms(self):
        try:
            with open(self.STORAGE_FILE, "r") as f:
                return json.load(f)
        except:
            return []

    def _save_alarms(self):
        with open(self.STORAGE_FILE, "w") as f:
            json.dump(self.alarms, f)

    def _load_pin_definitions(self):
        try:
            with open(self.PINDEF_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_pin_definitions(self):
        with open(self.PINDEF_FILE, "w") as f:
            json.dump(self.allowed_pins, f)

    async def sync_time(self):
        while True:
            gc.collect()
            try:
                ds = ds1302.DS1302(clk=Pin(1), dio=Pin(2), cs=Pin(3))
            except:
                print("Failed to initialize DS1302")

            try:
                t = ds.date_time()
                if t[0] == 2165 or t[1] == 165:
                    print("No RTC attached - check wiring!")
                else:
                    self.rtc.datetime((t[0], t[1], t[2], t[3], t[4], t[5], t[6], 0))
                    print(f"Clock synced successfully! {t[0]}-{t[1]:02d}-{t[2]:02d} {t[4]:02d}:{t[5]:02d}:{t[6]:02d}")

            except:
                print("RTC Sync failed - check wiring!")
            
            try:
                ntptime.settime()
                t = time.time() + self.offset
                tm = time.localtime(t)
                # ESP32 RTC: (y, m, d, wd, h, m, s, ss)
                self.rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
                ds.date_time((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5]))
                print(f"NTP Sync Successful {tm[0]}-{tm[1]:02d}-{tm[2]:02d} {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}")
                return True # Tell the caller we are done!
            except:
                print("NTP Sync Failed.")
                return False

    async def continuous_time_sync(self, sleep_interval=86400):
        print("Continuous Time Sync Task started...")
        while True:
            await asyncio.sleep(sleep_interval)
            await self.sync_time()

    async def continuous_subscribe(self, sleep_interval=30):
        print("Continuous subscribe Task started...")
        while True:
            await asyncio.sleep(sleep_interval)
            try:
                if self.subscribe_topic:
                    await self.subscribe(self.subscribe_topic)
                    # return True
            except Exception as e:
                print(f"Error occurred while subscribing: {e}")
                # return False

    async def continuous_publish_config(self, config_topic, config_payload, sleep_interval=30):
        print("Continuous Publish Config Task started...")
        while True:
            await asyncio.sleep(sleep_interval)
            self.mqtt.publish_config(config_topic, json.dumps(config_payload))

    async def formatted_message(self, alarm, msg):
        clean_name = alarm['pin_name'].lower().replace(" ", "_")
        data = {}
        data[clean_name] = msg
        return json.dumps(data) if data else "{}"

    async def formatted_homeassistant_message(self, name, msg):
        clean_name = name.lower().replace(" ", "_")
        data = {}
        data[clean_name] = msg
        return json.dumps(data) if data else "{}"

    async def _trigger_action(self, alarm):
        # 1. Initialize all pins in the list
        pins = [Pin(p_num, Pin.OUT) for p_num in alarm['pins']]
        
        action = alarm.get('action', 'pulse')
        name = alarm.get('name', 'Unnamed Alarm')
        pn = alarm.get('pin_name').replace(" ", "")
        state_topic = f"homeassistant/{alarm['type']}/{g.mac}/state"

        # Get current time for the print statement
        now = self.rtc.datetime()
        ts = f"{now[4]:02d}:{now[5]:02d}:{now[6]:02d}"

        # Pre-calculate state values based on active_low configuration
        on_value = 0 if alarm.get("active_low") == 1 else 1
        off_value = 1 if alarm.get("active_low") == 1 else 0

        if action == "on": 
            # 2. Turn ALL pins ON
            for p in pins:
                p.value(on_value)                        
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}ON"))
            except Exception as e:
                print(f"Error ON occurred while publishing MQTT message: {e}")

        elif action == "off": 
            # 3. Turn ALL pins OFF
            for p in pins:
                p.value(off_value)                        
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}OFF"))
            except Exception as e:
                print(f"Error OFF occurred while publishing MQTT message: {e}")

        elif action == "pulse":
            # 4. Pulse ON: Turn ALL pins ON immediately
            for p in pins:
                p.value(on_value)                        
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}ON"))
            except Exception as e:
                print(f"Error PULSE ON occurred while publishing MQTT message: {e}")
            
            # Non-blocking async sleep for duration
            await asyncio.sleep(int(alarm['duration']))
            
            # 5. Pulse OFF: Turn ALL pins OFF together
            for p in pins:
                p.value(off_value)                        
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}OFF"))
            except Exception as e:
                print(f"Error PULSE OFF occurred while publishing MQTT message: {e}")

    async def alarm_checker_loop(self):
        print("Alarm Checker Task started...")
        while True:
            gc.collect()
            now = self.rtc.datetime()
            wd, h, m = now[3], now[4], now[5]
            for al in self.alarms:
                al_h, al_m, al_s = al['time']
                if wd in al['days'] and h == al_h and m == al_m:
                    if not al.get('triggered_today', False):
                        al['triggered_today'] = True
                        asyncio.create_task(self._trigger_action(al))
                if m != al_m and al.get('triggered_today', False):
                    al['triggered_today'] = False
            await asyncio.sleep(10)

    def _setup_routes(self):
        @self.app.route('/get-time')
        async def get_time(request):
            now = self.rtc.datetime()
            current_time_str = f"{now[0]}-{now[1]:02d}-{now[2]:02d} {now[4]:02d}:{now[5]:02d}:{now[6]:02d}"
            current_day = self.DAY_NAMES[now[3]]
            return f"{current_day} {current_time_str}", 200, {'Content-Type': 'text/plain; charset=utf-8'}

        @self.app.route('/get-temp')
        async def get_temp(request):
                return f"{self.temp} {self.hum}", 200, {'Content-Type': 'text/plain; charset=utf-8'}

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
                
                # Convert the pins list back into a clean string (e.g. "1, 2") for display
                pins_display = ", ".join(str(p) for p in a.get('pins', []))
                
                # Updated the string template to reference pins_display instead of a['pin']
                rows += f"<li><strong>{name}</strong><br>{a['time'][0]:02d}:{a['time'][1]:02d} | {days_str} | Pins:{pins_display} | {action_label}{dur_info} <a class='del' href='/del?id={i}'>Delete</a></li>"
            
            day_boxes = "".join([f'<label><input type="checkbox" name="days" value="{i}" class="day-check" checked> {name}</label> ' for i, name in enumerate(self.DAY_NAMES)])
            pin_options = "".join([f'<option value="{name[0]}">{name[0]}</option>' 
                            for name in self.allowed_pins.items()])

            # --- PRE-BUILD THE OLED/TEMP DISPLAY HTML BLOCKS HERE ---
            temp_html_block = ""
            if self.temp is not None:
                temp_html_block = f"""
                <div class="temp-display">
                    <h3 id="live-temp">{self.temp} °C {self.hum} %</h3>
                    <div class="refresh-controls">
                        <button onclick="fetchLiveTemp()">↻ Refresh Temperature</button>
                        <span style="margin: 0 10px;">|</span>
                        <label>
                            <input type="checkbox" id="auto-refresh-toggle-temp" checked onchange="manageAutoRefreshTemp()"> Auto-Refresh (10s)
                        </label>
                    </div>
                </div>
                """


            html = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 20px; }}
                    .time-display {{ background: #333; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; border: 1px solid #03dac6; }}
                    .time-display h3 {{ margin: 0; color: #03dac6; }}
                    .temp-display {{ background: #333; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; border: 1px solid #03dac6; }}
                    .temp-display h3 {{ margin: 0; color: #03dac6; }}
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

                    let timerInstanceTemp = null;

                    async function fetchLiveTemp() {{
                        try {{
                            let res = await fetch('/get-temp');
                            if (res.ok) {{
                                let txt = await res.text();
                                document.getElementById('live-temp').innerText = txt;
                            }}
                        }} catch (err) {{
                            console.log("Temperature sync failure", err);
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
                    function manageAutoRefreshTemp() {{
                        const checkbox = document.getElementById('auto-refresh-toggle-temp');
                        if (checkbox.checked) {{
                            if (!timerInstanceTemp) {{
                                timerInstanceTemp = setInterval(fetchLiveTemp, 10000);
                            }}
                        }} else {{
                            clearInterval(timerInstanceTemp);
                            timerInstanceTemp = null;
                        }}
                    }}
                    
                    
                    window.addEventListener('DOMContentLoaded', function() {{
                        var devSelect = document.getElementById('dev-select');
                        if (devSelect) updateAlarmName(devSelect);
                        
                        // Initialize auto-refresh when the DOM finishes rendering
                        manageAutoRefresh();
                        manageAutoRefreshTemp();
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

                {temp_html_block}

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
        
        @self.app.route('/add')
        async def add(request):
            t_parts = request.args.get('t').split(':')
            days_raw = request.args.getlist('days')
            selected_days = [int(d) for d in days_raw] if days_raw else list(range(7))
            name_selection = request.args.get('pn')
            clean_name = name_selection.lower().replace(" ", "_")

            # 1. Update the check to extract the list of pins
            if name_selection in self.allowed_pins:
                actual_gpios = self.allowed_pins[name_selection]["pins"] # Changed from "pin" to "pins"
            else:
                return "Invalid Pin Selection", 400 

            self.alarms.append({
                "name": request.args.get('n', 'Alarm'),
                "time": [int(t_parts[0]), int(t_parts[1]), 0],
                "days": selected_days,
                "action": request.args.get('a'),
                "duration": int(float(request.args.get('d', 0))),
                "pins": actual_gpios,        # 2. Store the list of safe GPIO numbers
                "pin_name": name_selection,  # Helpful for displaying in the UI later
                "triggered_today": False,
                "type": self.allowed_pins[name_selection].get("type"),
                "active_low": self.allowed_pins[name_selection].get("active_low")
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


        # --- ROUTE 1: Display the Web Form ---
        @self.app.route('/config', methods=['GET'])
        async def show_config(request):
            json_content = self.allowed_pins
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ESP32 Pin Config</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: sans-serif; margin: 20px; background: #222; color: #fff; }}
                    textarea {{ width: 100%; height: 400px; font-family: monospace; background: #111; color: #a6e22e; border: 1px solid #444; padding: 10px; box-sizing: border-box; }}
                    .btn {{ display: inline-block; background: #28a745; color: white; border: none; padding: 10px 20px; text-decoration: none; cursor: pointer; margin-top: 10px; font-size: 16px; border-radius: 4px; }}
                    .btn-home {{ background: #007bff; margin-left: 10px; }}
                    .actions {{ margin-top: 15px; }}
                </style>
            </head>
            <body>
                <h2>Edit Hardware Configuration</h2>
                <form method="POST" action="/config">
                    <textarea name="json_data">{json_content}</textarea>
                    <div class="actions">
                        <input type="submit" class="btn" value="Save Changes">
                        <a href="/" class="btn btn-home">Return Home</a>
                    </div>
                </form>
            </body>
            </html>
            """
            return html, 200, {'Content-Type': 'text/html'}

        # --- ROUTE 2: Handle Save, Reload Variable, and Show Options ---
        @self.app.route('/config', methods=['POST'])
        async def save_config(request):
            global my_runtime_variable  # Reference your main configuration variable
            raw_json = request.form.get('json_data', '{}').replace("'", '"')
            
            try:
                # Validate JSON format
                json.loads(raw_json)
                # 1. Save to the file system
                self._save_pin_definitions()
                # 2. Update the live variable in memory instantly
                self.allowed_pins = raw_json
                print("Config updated live in memory!")
                return "", 302, {'Location': '/config'}

            except ValueError as e:
                return f"<h3>JSON Syntax Error! Config not saved.</h3><p>{str(e)}</p><a href='/config'>Go Back</a>"


    async def mqtt_send_dht_loop(self):
        print("MQTT DHT Sender Task started...")
        while True:
            try:
                self.dht_sensor.measure()
                self.temp = self.dht_sensor.temperature()
                self.hum = self.dht_sensor.humidity()
                payload = json.dumps({"esp32_s2_temperature": self.temp, "esp32_s2_humidity": self.hum})
                self.mqtt.publish(f"homeassistant/sensor/{g.mac}/state", payload)
            except Exception as e:
                print(f"Error occurred while sending DHT data via MQTT: {e}")
                self.temp = "N/A"
                self.hum = "N/A"
            await asyncio.sleep(10)  # Send every 10 seconds

    async def mqtt_send_ds18x20_loop(self):
        loop_counter = 0  # Tracks elapsed seconds
        while True:
            loop_counter += 1
            # 2. If no sensors were found initially, warn and wait before trying again
            if not self.roms:
                print("No sensors found. Check your wiring and pull-up resistor.")
                await asyncio.sleep(10)
                
                # Optional: Attempt a rescue rescan if you want to support hot-plugging
                try:
                    self.roms = self.ds_sensor.scan()
                except:
                    pass
                continue

            try:
                # Start temperature conversion across all sensors
                self.ds_sensor.convert_temp()
                
                # Yield control during the 750ms conversion time
                await asyncio.sleep_ms(750)
                
                # Read data from each discovered sensor
                for rom in self.roms:
                    rom_address = ''.join(['{:02x}'.format(b) for b in rom])
                    temp_c = self.ds_sensor.read_temp(rom)
                    
                    print(f"{rom_address} Temp: {temp_c:.2f}°C")
                    
                    # Store the last read value for your Web UI f-string variable!
                    self.temp = f"{temp_c:.1f}"
                    # (Make sure self.hum is also initialized to something like "N/A" or 0)

                    # Check if the address doesn't exist in your mapping dictionary
                    if rom_address not in self.CALIBRATION_MAP:
                        print(f"ALERT: Unregistered sensor found! ROM: {rom_address}")
                    
                    # Grab calibration tuple or default to safe uncalibrated bypass (1.0, 0.0)
                    multiplier, offset = self.CALIBRATION_MAP.get(rom_address, (1.0, 0.0))
                    
                    # Calculate real temperature: (reading * m) + c
                    calibrated_temp = (temp_c * multiplier) + offset

                    # 1. Update the OLED display safely
                    await self.write_ds18x20_to_oled(f"  {temp_c:.2f}  ", 1)
                    try:
                        payload = json.dumps({"esp32_s2_dallas_temperature": temp_c})
                        self.mqtt.publish(f"homeassistant/sensor/{g.mac}/state", payload)
                        
                    except Exception as mqtt_err:
                        print(f"Network warning: Could not publish state over MQTT ({mqtt_err})")

            except Exception as e:
                print("Error reading sensor:", e)
                
            await asyncio.sleep(10)  # Send every 10 seconds

    async def mqtt_listener_loop(self):
        print("MQTT Listener started...")
        last_healthy_time = time.time()
        TIMEOUT_SEC = 30  # Passive 30 second gate timer baseline

        while True:
            try:
                # check_msg() is non-blocking in most libraries; 
                # it just checks the socket buffer once and moves on.
                self.mqtt.check_msg()
                last_healthy_time = time.time()
            except Exception as e:
                print(f"MQTT Listener Error: {e}")
            # This sleep is CRITICAL to let the Web Server and Alarms run
            await asyncio.sleep(1) 

            # 2. Evaluate if network or MQTT connection has been dead for 15 minutes
            if (time.time() - last_healthy_time) > TIMEOUT_SEC:
                print(f"System link down for {TIMEOUT_SEC} secs. Running passive network recovery...")
                try:
                    sta_if = network.WLAN(network.STA_IF)
                    # Step A: Reconnect Wi-Fi asynchronously if the router dropped
                    if not sta_if.isconnected():
                        print("Router link down. Starting background Wi-Fi recovery...")
                        await WIFI.reconnect_wifi_async()
                        gc.collect()

                    # Step B: Rebuild MQTT architecture if Wi-Fi interface is valid
                    if sta_if.isconnected():
                        print("Wi-Fi network confirmed. Restoring MQTT client context...")
                        try:
                            await WIFI.reconnect_wifi_async()
                            print("disconnecting frm MQTT...")
                            self.mqtt.disconnect()
                        except Exception:
                            pass
                        gc.collect()
                        await asyncio.wait_for(self.connect_mqtt_async(), timeout=15)
                        await asyncio.wait_for(self.subscribe(self.subscribe_topic), timeout=15)
                        print("Network communication pipeline completely restored.")
                    else:
                        print("Router infrastructure still down. Local tasks operating natively...")
                        
                except Exception as recovery_error:
                    print(f"Recovery cycle deferred: {recovery_error}")
                    retry_subscribe = True
                    gc.collect()

                # Advance baseline pointer to maintain non-aggressive spacing between checks
                last_healthy_time = time.time()

            # Essential yield step keeps the Web Server and Alarm loops completely unblocked
            await asyncio.sleep(1)

    async def connect_mqtt_async(self):
        """Encapsulates synchronous connect script blocks inside non-blocking routines."""
        try:
            await self.mqtt.connect()
            return True
        except Exception as e:
            print(f"Error occurred connect_mqtt_async: {e}")
        await asyncio.sleep_ms(10)
        return False


    async def subscribe(self, topic):
        self.mqtt.subscribe(topic) 
        await asyncio.sleep(1)

    async def mqtt_processor_loop(self):
        print("MQTT Processor Task started...")
        while True:
            if len(self.mqtt.queue) > 0:
                topic, msg = self.mqtt.queue.popleft()
                # Iterate through your allowed_pins dictionary
                for name, config in self.allowed_pins.items():
                    # Check if the message matches a "Turn On" command
                    payload = name.replace(" ", "")
                    
                    if msg == f"{payload}ON":          
                        # Initialize all pins mapped to this device configuration
                        pins = [Pin(p_num, Pin.OUT) for p_num in config['pins']]
                        on_value = 0 if config.get("active_low") == 1 else 1
                        
                        # Turn ALL pins ON
                        for p in pins:
                            p.value(on_value)                        
                        try:
                            self.mqtt.publish(config['state_topic'], await self.formatted_homeassistant_message(name, f"{msg}"))
                        except Exception as e:
                            print(f"Error ON occurred while publishing MQTT message: {e}")             
                    
                    # Check if it matches a "Turn Off" command
                    elif msg == f"{payload}OFF":
                        # Initialize all pins mapped to this device configuration
                        pins = [Pin(p_num, Pin.OUT) for p_num in config['pins']]
                        off_value = 1 if config.get("active_low") == 1 else 0
                        
                        # Turn ALL pins OFF
                        for p in pins:
                            p.value(off_value)
                        try:
                            self.mqtt.publish(config['state_topic'], await self.formatted_homeassistant_message(name, f"{msg}"))
                        except Exception as e:
                            print(f"Error OFF occurred while publishing MQTT message: {e}")
            await asyncio.sleep(0.1)
        
    async def announce_to_home_assistant(self,mac):
        count = 0
        for name, info in self.allowed_pins.items():
            clean_name = name.lower().replace(" ", "_")
            payload = name.replace(" ", "")
            type = info.get("type", "sensor")


            while mac is None:
                print("MAC address is None, waiting for hardware initialization...")
                await asyncio.sleep(1)
                try:
                    wlan_interface = network.WLAN(network.STA_IF)
                    raw_mac = wlan_interface.config('mac')
                    if raw_mac:
                        g.mac = ''.join(['%02x' % b for b in raw_mac])
                except Exception:
                    pass
                mac = g.mac  # Re-evaluate local variable to break the loop

                
            # mac = g.mac  # Use the global MAC address variable
            # while mac is None:
            #     print("MAC address is None, waiting for it to be set...")
            #     await asyncio.sleep(1)
            #     mac = g.mac  # Re-check the global MAC address variable
            base_topic = f"homeassistant/{type}/{mac}"

            # 1. Start with the mandatory fields
            config_payload = {
                "name": name,
                "unique_id": f"esp32_{clean_name}",
                "state_topic": f"{base_topic}/state",
                "value_template": "{{ value_json." + clean_name + " }}",
                "device": {
                    "identifiers": [f"esp32_{mac}"],
                    "name": "ESP32 Smart Hub with Temperature and Humidity",
                    "model": "ESP32 S2 MINI"
                }
            }

            # 2. Only add optional items if they have a value
            if info.get("device_class"):
                config_payload["device_class"] = info["device_class"]

            # 3. If you are adding the Switch functionality we discussed:
            if type == "switch":
                config_payload["command_topic"] = f"{base_topic}/subscribe"
                config_payload["payload_on"] = f"{payload}ON"
                config_payload["payload_off"] = f"{payload}OFF"

            if type == "sensor":
                addon = info["value_template_addon"]
                config_payload["unit_of_measurement"] = info["unit_of_measurement"]
                config_payload["value_template"] = "{{ value_json." + clean_name + addon + " }}" 


 

            self.subscribe_topic = f"{base_topic}/subscribe"
            config_topic = f"{base_topic}/{clean_name}/config"
            self.allowed_pins[name]["state_topic"] = config_payload["state_topic"]
            self.allowed_pins[name]["config_topic"] = config_topic
            try:
                if count == 0:
                    asyncio.create_task(self.subscribe(f"{self.subscribe_topic}"))
                count = 1
                self.mqtt.publish_config(config_topic, json.dumps(config_payload))
                print(f"Published Home Assistant config for {name} to {config_topic}")
            except Exception as e:
                print(f"Error occurred while publishing MQTT config for {name}: {e}")

    async def run(self):
        count = 0
        while not await self.sync_time() and count < 5:  # Try syncing time up to 5 times
            print("Initial sync failed, retrying...")
            await asyncio.sleep(1)
            count += 1

        try:
            self.mqtt.connect()
        except Exception as e:
            print(f"Error in run occurred while connecting to MQTT: {e}")

        try:
            await asyncio.sleep(2)
            asyncio.create_task(self.announce_to_home_assistant(g.mac))
            asyncio.create_task(self.mqtt_listener_loop())
            asyncio.create_task(self.mqtt_processor_loop())
            if self.dht_sensor is not None:
                asyncio.create_task(self.mqtt_send_dht_loop())
            print("len(self.roms):", len(self.roms))
            if len(self.roms) > 0:
                asyncio.create_task(self.mqtt_send_ds18x20_loop())

        except Exception as e:
            print(f"Error in run subscribe, publish in MQTT: {e}")

        asyncio.create_task(self.continuous_time_sync())
        asyncio.create_task(self.alarm_checker_loop())
        print("Server running on port 80...")
        await self.app.start_server(port=80)

# --- 3. Entry Point ---
if __name__ == "__main__":
    manager = SmartHomeManager()
    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        pass