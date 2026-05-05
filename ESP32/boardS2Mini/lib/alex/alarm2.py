import asyncio
import ntptime, time, json, os
from machine import Pin, RTC

# --- PERSISTENCE HELPERS ---
STORAGE_FILE = "alarms.json"

def save_alarms(alarms_data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(alarms_data, f)

def load_alarms():
    try:
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    except:
        return []


# Define your hardware pins
light_pin = Pin(2, Pin.OUT)
timed_pin = Pin(4, Pin.OUT)

class AsyncAlarmManager(PersistentAlarmManager):
    def add_duration_alarm(self, days, h, m, s, duration, pin_id):
        # 'duration' is in seconds. If duration is 0, it's a permanent state change.
        self.alarms.append({
            'days': days,
            'time': [h, m, s],
            'duration': duration,
            'pin': pin_id,
            'triggered_today': False
        })
        save_alarms(self.alarms)

    def check(self):
        now = self.rtc.datetime()
        weekday, h, m, s = now[3], now[4], now[5], now[6]

        for alarm in self.alarms:
            al_h, al_m, al_s = alarm['time']
            
            if (weekday in alarm['days'] and h == al_h and m == al_m and s == al_s 
                and not alarm['triggered_today']):
                
                alarm['triggered_today'] = True
                save_alarms(self.alarms)
                
                # Execute Logic
                asyncio.create_task(self.trigger_action(alarm))

            # Reset logic
            if h != al_h or m != al_m:
                if alarm['triggered_today']:
                    alarm['triggered_today'] = False
                    save_alarms(self.alarms)

    async def trigger_action(self, alarm):
        pin = Pin(alarm['pin'], Pin.OUT)
        print(f"Triggering Pin {alarm['pin']}")
        
        pin.value(1) # Turn ON
        
        # If there is a duration, wait and turn OFF
        if alarm['duration'] > 0:
            await asyncio.sleep(alarm['duration'])
            pin.value(0)
            print(f"Pin {alarm['pin']} turned OFF after {alarm['duration']}s")
