# buzzer.py


from machine import Pin, PWM
import time

# 1. Initialize PWM on a specific GPIO pin (e.g., Pin 15)
# Set the initial frequency (e.g., 1000 Hz)
buzzer = PWM(Pin(15), freq=1000, duty_u16=0)

def play_tone(frequency, duration_ms):
    if frequency > 0:
        buzzer.freq(frequency)
        buzzer.duty_u16(32768)  # 50% duty cycle for square wave
    
    time.sleep_ms(duration_ms)
    buzzer.duty_u16(0)         # Stop the sound
    print(f"Playing {frequency}Hz for {duration_ms}ms")

# Frequencies for "Happy Birthday" melody (in Hz)
# Notes: C4=262, D4=294, E4=330, F4=349, G4=392, A4=440, B4=494, C5=523
notes = {
    'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494,
    'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784
}

# Melody sequence: (note, duration in ms)
melody = [
    ('G4', 400), ('G4', 400), ('A4', 800), ('G4', 800), ('C5', 800), ('B4', 1600),
    ('G4', 400), ('G4', 400), ('A4', 800), ('G4', 800), ('D5', 800), ('C5', 1600),
    ('G4', 400), ('G4', 400), ('G5', 800), ('E5', 800), ('C5', 800), ('B4', 800), ('A4', 1600),
    ('F5', 400), ('F5', 400), ('E5', 800), ('C5', 800), ('D5', 800), ('C5', 1600)
]

# Play the melody
for note, duration in melody:
    play_tone(notes.get(note, 0), duration)
    time.sleep_ms(100)  # Short pause between notes


# 3. Clean up (optional)
buzzer.deinit()