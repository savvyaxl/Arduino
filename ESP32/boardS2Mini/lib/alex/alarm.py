import ntptime # type: ignore
import time
from machine import RTC # type: ignore

class TimeSync:
    def __init__(self, base_utc_offset=-5):
        self.rtc = RTC()
        self.base_offset = base_utc_offset * 3600 # Base offset in seconds
        self.last_ntp_sync = 0

        self.sync_ntp()

    def sync_ntp(self):
        """Fetches UTC and adjusts for Timezone + DST."""
        try:
            ntptime.settime()
            local_seconds = time.time() + self.base_offset
            tm = time.localtime(local_seconds)
            # ESP32 RTC tuple: (year, month, day, weekday, hour, minute, second, subsecond)
            # Note: weekday index 6 in time.localtime() is index 3 in RTC.datetime()
            self.rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
            self.last_ntp_sync = time.time()
            print("Sync complete. Current weekday:", tm[6])
            print(f"Current datetime: {self.getTime()}")
        except:
            print("Sync failed")
            # wait 10 seconds and try again
            time.sleep(10)
            self.sync_ntp()

    def getTime(self):
        dt = self.rtc.datetime()
        return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"
    
                
class AlarmDaily:
    def __init__(self):
        self.rtc = RTC()
        self.alarms = []
        self.ticker = time.time()

    def add_alarm(self, hour, minute, second, callback):
        self.alarms.append({'time': (hour, minute, second), 'started': False, 'action': callback})

    def check_alarms(self):
        now = self.rtc.datetime()
        # if now[6] == 0: # Check at the start of the minute
        for alarm in self.alarms:
            if now[4] == alarm['time'][0] and now[5] == alarm['time'][1] and now[6] == alarm['time'][2] and not alarm['started']:
                alarm['started'] = True
                alarm['action']()

    def list_alarms(self):
        for alarm in self.alarms:
            print(f"Alarm set for {alarm['time'][0]:02d}:{alarm['time'][1]:02d}:{alarm['time'][2]:02d}")

class AlarmWeekly:
    def __init__(self):
        self.rtc = RTC()
        self.alarms = []
        
    def add_weekly_alarm(self, days, hour, minute, second, callback):
        """
        days: list of integers (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun)
        Example: [0, 2, 4] for Mon, Wed, Fri
        """
        if isinstance(days, int): days = [days] # Support single day integer
        self.alarms.append({'days': days, 'time': (hour, minute, second), 'started': False, 'action': callback})

    def check_alarms(self):
        # rtc.datetime returns (year, month, day, weekday, hour, minute, second, subsecond)
        now = self.rtc.datetime()
        weekday, hour, minute, second = now[3], now[4], now[5], now[6]

        for alarm in self.alarms:
            al_h, al_m, al_s = alarm['time']
            if weekday in alarm['days'] and hour == al_h and minute == al_m and second == al_s and not alarm['started']:
                alarm['action']()
                alarm['started'] = True

    def list_alarms(self):
        for alarm in self.alarms:
            days_str = ','.join(str(d) for d in alarm['days'])
            print(f"Alarm set for days {days_str} at {alarm['time'][0]:02d}:{alarm['time'][1]:02d}:{alarm['time'][2]:02d}")

