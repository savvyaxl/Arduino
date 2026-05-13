import uasyncio as asyncio # type: ignore
import json, ntptime, time, os, ds1302 # type: ignore
from machine import RTC, Pin # type: ignore
from microdot.microdot import Microdot
import gc, network # type: ignore
from mysecrets import secrets
import alex.mqtt as MQTT
import globals as g

class SmartHomeManager:
    STORAGE_FILE = "alarms.json"
    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, utc_offset=-3):
        self.rtc = RTC()
        self.offset = utc_offset * 3600
        self.alarms = self._load_alarms()
        self.app = Microdot()
        self._setup_routes()
        self.mqtt = MQTT.MQTTHandler()
        #self.mqtt.client.set_callback(self.handle_mqtt_command)
        # self.allowed_pins = {
        #     "Light": {
        #         "pin": 15,
        #         "value": "light_state",
        #         "value_template": "{{ value_json.light_state }}",
        #         "unit": "",
        #         "device_class": "None"
        #     },
        #     "Water Pump": {
        #         "pin": 4,
        #         "value": "pump_status",
        #         "value_template": "{{ value_json.pump_status }}",
        #         "unit": "",
        #         "device_class": "None"
        #     }
        # }
        self.allowed_pins = {
            "Water Pump 3": {
                "type": "switch", # Change domain to switch
                "pin": 4,
                "state_topic": f"homeassistant/switch/{g.mac}/state",
                "command_topic": f"homeassistant/switch/{g.mac}/subscribe",
                "payload_on": "WaterPump3ON",
                "payload_off": "WaterPump3OFF",
                "value_template": "{{{{ value_json.water_pump }}}}"
            },
            "Water Pump 4": {
                "type": "switch", # Change domain to switch
                "pin": 6,
                "state_topic": f"homeassistant/switch/{g.mac}/state",
                "command_topic": f"homeassistant/switch/{g.mac}/subscribe",
                "payload_on": "WaterPump4ON",
                "payload_off": "WaterPump4OFF",
                "value_template": "{{{{ value_json.water_pump }}}}"
            },

        }

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

    async def sync_time(self):
        while True:
            gc.collect()
            try:
                ds = ds1302.DS1302(clk=Pin(1), dio=Pin(2), cs=Pin(3))
            except:
                print("Failed to initialize DS1302")

            try:
                t = ds.date_time()
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
        p = Pin(alarm['pin'], Pin.OUT)
        action = alarm.get('action', 'pulse')
        name = alarm.get('name', 'Unnamed Alarm')
        base_topic = f"homeassistant/sensor/{g.mac}"
        pn = alarm.get('pin_name').replace(" ", "")
        state_topic = f"homeassistant/{alarm['type']}/{g.mac}/state"

        # Get current time for the print statement
        now = self.rtc.datetime()
        ts = f"{now[4]:02d}:{now[5]:02d}:{now[6]:02d}"
        
        print(f"ALARM TRIGGERED: '{name}' at {ts} | Action: {action.upper()}")

        if action == "on": 
            p.value(1)
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}ON"))
            except Exception as e:
                print(f"Error ON occurred while publishing MQTT message: {e}")
        elif action == "off": 
            p.value(0)
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}OFF"))
            except Exception as e:
                print(f"Error OFF occurred while publishing MQTT message: {e}")
        elif action == "pulse":
            p.value(1)
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}ON"))
            except Exception as e:
                print(f"Error PULSE ON occurred while publishing MQTT message: {e}")
            await asyncio.sleep(int(alarm['duration']))
            p.value(0)
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}OFF"))
            except Exception as e:
                print(f"Error PULSE OFF occurred while publishing MQTT message: {e}")
            print(f"ALARM FINISHED: '{name}' pulse complete.")

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
            pin_options = "".join([f'<option value="{name[0]}">{name[0]}</option>' 
                            for name in self.allowed_pins.items()])

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
                    Device: <select name="pn">
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
            name_selection = request.args.get('pn')
            clean_name = name_selection.lower().replace(" ", "_")

            if name_selection in self.allowed_pins:
                actual_gpio = self.allowed_pins[name_selection]["pin"]
            else:
                return "Invalid Pin Selection", 400 

            self.alarms.append({
                "name": request.args.get('n', 'Alarm'),
                "time": [int(t_parts[0]), int(t_parts[1]), 0],
                "days": selected_days,
                "action": request.args.get('a'),
                "duration": int(float(request.args.get('d', 0))),
                "pin": actual_gpio,        # Store the safe GPIO number
                "pin_name": name_selection, # Helpful for displaying in the UI later
                "triggered_today": False,
                "type": self.allowed_pins[name_selection].get("type")
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

    async def mqtt_listener_loop(self):
        print("MQTT Listener started...")
        while True:
            try:
                # check_msg() is non-blocking in most libraries; 
                # it just checks the socket buffer once and moves on.
                self.mqtt.check_msg() 
            except Exception as e:
                print(f"MQTT Listener Error: {e}")
                # Optional: try to reconnect here if the connection dropped
            
            # This sleep is CRITICAL to let the Web Server and Alarms run
            await asyncio.sleep(1) 

    async def subscribe(self, topic):
        print("MQTT subscribe started...")
        self.mqtt.subscribe(topic) 
        await asyncio.sleep(1)

    async def mqtt_processor_loop(self):
        print("MQTT Processor Task started...")
        while True:
            if len(self.mqtt.queue) > 0:
                topic, msg = self.mqtt.queue.popleft()
                print(f"Processing {topic}: {msg}")
                
                if "alarm" in msg:
                    print(f"Processing alarm command: {msg}")

                # Iterate through your allowed_pins dictionary
                for name, config in self.allowed_pins.items():
                    
                    # Check if the message matches a "Turn On" command
                    if msg == config["payload_on"]:
                        p = Pin(config['pin'], Pin.OUT)
                        print(f"Turning ON {name} on pin {p}")
                        p.value(1)
                        try:
                            pn = name.replace(" ", "")
                            self.mqtt.publish(config['state_topic'], await self.formatted_homeassistant_message(name, f"{pn}ON"))
                        except Exception as e:
                            print(f"Error ON occurred while publishing MQTT message: {e}")
                    
                    # Check if it matches a "Turn Off" command
                    elif msg == config["payload_off"]:
                        p = Pin(config['pin'], Pin.OUT)
                        print(f"Turning OFF {name} on pin {p}")
                        p.value(0)
                        try:
                            pn = name.replace(" ", "")
                            self.mqtt.publish(config['state_topic'], await self.formatted_homeassistant_message(name, f"{pn}OFF"))
                        except Exception as e:
                            print(f"Error OFF occurred while publishing MQTT message: {e}")


            await asyncio.sleep(0.1)
        
    async def announce_to_home_assistant(self):
        base_topic = f"homeassistant/sensor/{g.mac}"

        for name, info in self.allowed_pins.items():
            clean_name = name.lower().replace(" ", "_")
            if info.get("type") == "switch":
                base_topic = f"homeassistant/switch/{g.mac}"
            if info.get("type") == "binary_sensor":
                base_topic = f"homeassistant/binary_sensor/{g.mac}"

            # 1. Start with the mandatory fields
            config_payload = {
                "name": name,
                "unique_id": f"esp32_{clean_name}",
                "state_topic": f"{base_topic}/state",
                "value_template": "{{ value_json." + clean_name + " }}",
                "device": {
                    "identifiers": [f"esp32_{g.mac}"],
                    "name": "ESP32 Smart Hub"
                }
            }

            # 2. Only add optional items if they have a value
            if info.get("unit"):
                config_payload["unit_of_measurement"] = info["unit"]

            if info.get("device_class"):
                config_payload["device_class"] = info["device_class"]

            # 3. If you are adding the Switch functionality we discussed:
            if info.get("type") == "switch":
                config_payload["command_topic"] = f"{base_topic}/subscribe"
                config_payload["payload_on"] = info["payload_on"]
                config_payload["payload_off"] = info["payload_off"] 



            # Publish to: homeassistant/sensor/84f3eb23ea09/water_pump/config
            config_topic = f"{base_topic}/{clean_name}/config"
            try:
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
            asyncio.create_task(self.subscribe(f"homeassistant/switch/{g.mac}/subscribe"))
            asyncio.create_task(self.announce_to_home_assistant())
            asyncio.create_task(self.mqtt_listener_loop())
            asyncio.create_task(self.mqtt_processor_loop())
        except Exception as e:
            print(f"Error in run occurred while connecting to MQTT: {e}")

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