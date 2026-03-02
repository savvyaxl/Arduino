from machine import Pin, PWM
import time

class Buzzer:
    def __init__(self, pin=15):
        # Initialize PWM on the given pin
        self.buzzer = PWM(Pin(pin), freq=1000, duty_u16=0)

        # Frequencies for notes
        self.notes = {
            'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349,
            'G4': 392, 'A4': 440, 'B4': 494,
            'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784
        }

        # Default melody (Happy Birthday)
        self.melody = [
            ('G4', 400), ('G4', 400), ('A4', 800), ('G4', 800), ('C5', 800), ('B4', 1600),
            ('G4', 400), ('G4', 400), ('A4', 800), ('G4', 800), ('D5', 800), ('C5', 1600),
            ('G4', 400), ('G4', 400), ('G5', 800), ('E5', 800), ('C5', 800), ('B4', 800), ('A4', 1600),
            ('F5', 400), ('F5', 400), ('E5', 800), ('C5', 800), ('D5', 800), ('C5', 1600)
        ]

    def play_tone(self, frequency, duration_ms):
        """Play a single tone at given frequency and duration."""
        if frequency > 0:
            self.buzzer.freq(frequency)
            self.buzzer.duty_u16(32768)  # 50% duty cycle
        time.sleep_ms(duration_ms)
        self.buzzer.duty_u16(0)
        print(f"Playing {frequency}Hz for {duration_ms}ms")

    def play_melody(self, melody=None):
        """Play a melody sequence. Defaults to Happy Birthday."""
        if melody is None:
            melody = self.melody
        for note, duration in melody:
            self.play_tone(self.notes.get(note, 0), duration)
            time.sleep_ms(100)  # short pause between notes
        self.buzzer.duty_u16(0)

    def deinit(self):
        """Release the PWM resource."""
        self.buzzer.deinit()
