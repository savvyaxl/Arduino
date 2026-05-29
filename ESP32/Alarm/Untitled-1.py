        # Ensure name_selection is treated as a list even if it is a single item
        if not isinstance(name_selection, list):
            name_selections = [name_selection]
        else:
            name_selections = name_selection

        actual_gpios = []
        for ns in name_selections:
            if ns in self.allowed_pins:
                actual_gpios.append(self.allowed_pins[ns]["pin"])
            else:
                return f"Invalid Pin Selection: {ns}", 400

        # When appending to self.alarms, save the arrays and shared attributes:
        # Use the first pin selection to grab common fields like type and active_low
        first_ns = name_selections[0] 
        
        self.alarms.append({
            "name": request.args.get('n', 'Alarm'),
            "time": [int(t_parts[0]), int(t_parts[1]), 0],
            "days": selected_days,
            "action": request.args.get('a'),
            "duration": int(float(request.args.get('d', 0))),
            "pins": actual_gpios,  # Changed from "pin" to "pins"
            "pin_name": ", ".join(name_selections), 
            "triggered_today": False,
            "type": self.allowed_pins[first_ns].get("type"),
            "active_low": self.allowed_pins[first_ns].get("active_low")
        })



async def _trigger_action(self, alarm):
        # Initialize all pins in the list
        pins = [Pin(pin_num, Pin.OUT) for pin_num in alarm['pins']]
        
        action = alarm.get('action', 'pulse')
        name = alarm.get('name', 'Unnamed Alarm')
        pn = alarm.get('pin_name').replace(" ", "")
        state_topic = f"homeassistant/{alarm['type']}/{g.mac}/state"

        # Get current time for the print statement
        now = self.rtc.datetime()
        ts = f"{now[4]:02d}:{now[5]:02d}:{now[6]:02d}"

        if action == "on": 
            on_value = 0 if alarm.get("active_low") == 1 else 1
            for p in pins:
                p.value(on_value)                        
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}ON"))
            except Exception as e:
                print(f"Error ON occurred while publishing MQTT message: {e}")
                
        elif action == "off": 
            off_value = 1 if alarm.get("active_low") == 1 else 0
            for p in pins:
                p.value(off_value)                        
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}OFF"))
            except Exception as e:
                print(f"Error OFF occurred while publishing MQTT message: {e}")
                
        elif action == "pulse":
            on_value = 0 if alarm.get("active_low") == 1 else 1
            for p in pins:
                p.value(on_value)                        
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}ON"))
            except Exception as e:
                print(f"Error PULSE ON occurred while publishing MQTT message: {e}")
                
            await asyncio.sleep(int(alarm['duration']))
            
            off_value = 1 if alarm.get("active_low") == 1 else 0
            for p in pins:
                p.value(off_value)                        
            try:
                self.mqtt.publish(state_topic, await self.formatted_message(alarm, f"{pn}OFF"))
            except Exception as e:
                print(f"Error PULSE OFF occurred while publishing MQTT message: {e}")




        # Fallback helper for old individual pin entries
        pin_list = alarm.get('pins', [alarm.get('pin')])
        pins = [Pin(pin_num, Pin.OUT) for pin_num in pin_list if pin_num is not None]



            # Use getlist to capture multiple 'pn' query parameters
            names_raw = request.args.getlist('pn')
            
            # Fallback if your UI only sent a single string parameter instead of an array
            if not names_raw and name_selection:
                names_raw = [name_selection]

            actual_gpios = []
            for ns in names_raw:
                if ns in self.allowed_pins:
                    actual_gpios.append(self.allowed_pins[ns]["pin"])
                else:
                    return f"Invalid Pin Selection: {ns}", 400

            # Use the first valid selection to grab global configuration keys (like type, active_low)
            primary_name = names_raw[0]

            self.alarms.append({
                "name": request.args.get('n', 'Alarm'),
                "time": [int(t_parts[0]), int(t_parts[1]), 0],
                "days": selected_days,
                "action": request.args.get('a'),
                "duration": int(float(request.args.get('d', 0))),
                "pins": actual_gpios,  # Storing as an array: [1, 5]
                "pin_name": ", ".join(names_raw), # Helper for displaying combination in UI
                "triggered_today": False,
                "type": self.allowed_pins[primary_name].get("type"),
                "active_low": self.allowed_pins[primary_name].get("active_low")
            })
