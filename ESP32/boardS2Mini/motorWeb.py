from machine import Pin, PWM
import socket

# 1. Setup PWM
pwm_pin = Pin(33)
pwm = PWM(pwm_pin, freq=1000, duty_u16=32768) # Default: 1kHz, 50% duty

# 2. Web Server Setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        
        # Simple routing logic
        if "/update" in request:
            # Check for duty cycle (speed) update
            if "speed=" in request:
                speed = int(request.split("speed=")[1].split(" ")[0])
                pwm.duty_u16(max(0, min(65535, speed)))
            
            # Check for frequency update
            if "freq=" in request:
                freq = int(request.split("freq=")[1].split(" ")[0])
                # ESP32 usually supports 1Hz to 40MHz, but 1-20000Hz is common for motors
                pwm.freq(max(1, min(20000, freq)))
            
            # Send a quick "OK" so the page doesn't hang
            conn.send("HTTP/1.1 204 No Content\r\n\r\n")
        else:
            # Main UI with two sliders
            body = f"""
            <h1>ESP32 Control</h1>
            
            <p><strong>Speed (Duty):</strong> <span id="sVal">{pwm.duty_u16()}</span></p>
            <input type="range" min="0" max="65535" value="{pwm.duty_u16()}" 
                oninput="update('speed', this.value)">
            
            <p><strong>Frequency (Hz):</strong> <span id="fVal">{pwm.freq()}</span></p>
            <input type="range" min="1" max="20000" value="{pwm.freq()}" 
                oninput="update('freq', this.value)">

            <script>
            function update(type, val) {{
                document.getElementById(type == 'speed' ? 'sVal' : 'fVal').innerText = val;
                fetch('/update?' + type + '=' + val);
            }}
            </script>
            """
            
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body>" + body + "</body></html>"
            conn.send(response.encode())
        
        conn.close()
    except Exception as e:
        print("Error:", e)
        if 'conn' in locals(): conn.close()
