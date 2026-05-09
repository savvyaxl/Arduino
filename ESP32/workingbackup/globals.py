import json

myssid = None
mypass = None
broker = None
mqport = None
mquser = None
mqpass = None
mac = None
ip = None


def format_time2(t):
    return "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(
        t.tm_year, t.tm_mon, t.tm_mday,
        t.tm_hour, t.tm_min, t.tm_sec
    )

def format_time(t):
    return "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )
