# board.py – LOLIN S2 Mini (ESP32-S2FN4R2)
# Full GPIO aliasing + preconfigured buses for MicroPython

import machine # type: ignore

# Pin dictionary based on full board mapping
pins = {
    # Power and control
    "LED": machine.Pin(15, machine.Pin.OUT),   # Onboard LED
    "BUTTON": machine.Pin(0, machine.Pin.IN),  # Boot button

    # Power rails (not GPIOs, listed for reference)
    "5V": None,
    "3V3": None,
    "GND": None,

    # GPIO aliases
    "IO1": machine.Pin(1),
    "IO2": machine.Pin(2),
    "IO3": machine.Pin(3),
    "IO4": machine.Pin(4),
    "IO5": machine.Pin(5),
    "IO6": machine.Pin(6),
    "IO7": machine.Pin(7),
    "IO8": machine.Pin(8),
    "IO9": machine.Pin(9),
    "IO10": machine.Pin(10),
    "IO11": machine.Pin(11),
    "IO12": machine.Pin(12),
    "IO13": machine.Pin(13),
    "IO14": machine.Pin(14),
    "IO15": machine.Pin(15),
    "IO16": machine.Pin(16),
    "IO17": machine.Pin(17),
    "IO18": machine.Pin(18),
    "IO21": machine.Pin(21),
    "IO33": machine.Pin(33),
    "IO34": machine.Pin(34),
    "IO35": machine.Pin(35),
    "IO36": machine.Pin(36),
    "IO37": machine.Pin(37),
    "IO38": machine.Pin(38),
    "IO39": machine.Pin(39),
    "IO40": machine.Pin(40),

    # I2C default
    "SDA": machine.Pin(33),
    "SCL": machine.Pin(35),

    # SPI default
    "MOSI": machine.Pin(35),
    "MISO": machine.Pin(37),
    "SCK": machine.Pin(36),
    "CS": machine.Pin(12),

    # UART default
    "TX": machine.Pin(43),
    "RX": machine.Pin(44),
}

# Attribute-style access (e.g., board.IO1)
def __getattr__(name):
    if name in pins:
        return pins[name]
    raise AttributeError(f"No such pin: {name}")

# Preconfigured I2C bus
def I2C(id=0, freq=400000):
    return machine.I2C(id, scl=pins["SCL"], sda=pins["SDA"], freq=freq)

# Preconfigured SPI bus
def SPI(id=1, baudrate=1000000, polarity=0, phase=0):
    return machine.SPI(id,
                       baudrate=baudrate,
                       polarity=polarity,
                       phase=phase,
                       sck=pins["SCK"],
                       mosi=pins["MOSI"],
                       miso=pins["MISO"])

# Preconfigured UART bus
def UART(id=1, baudrate=115200):
    return machine.UART(id, baudrate=baudrate, tx=pins["TX"], rx=pins["RX"])
