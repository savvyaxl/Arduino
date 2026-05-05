from machine import Pin, PWM # type: ignore
import socket

# 1. Setup PWM
pwm_pin = Pin(33)
pwm = PWM(pwm_pin, freq=1000, duty_u16=0) 

# 2. Web Server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        
        if "/update" in request:
            if "speed=" in request:
                speed = int(request.split("speed=")[1].split(" ")[0])
                pwm.duty_u16(max(0, min(65535, speed)))
            
            if "freq=" in request:
                freq = int(request.split("freq=")[1].split(" ")[0])
                pwm.freq(max(1, min(20000, freq)))
            
            conn.send("HTTP/1.1 204 No Content\r\n\r\n")
        else:
            # UI with Sliders and a BIG RED STOP BUTTON
            body = f"""
            <h1>ESP32 Control</h1>
            
            <p>Speed: <span id="sVal">{pwm.duty_u16()}</span></p>
            <input type="range" id="sSlider" min="0" max="65535" value="{pwm.duty_u16()}" 
                oninput="update('speed', this.value)">
            
            <p>Frequency (Hz): <span id="fVal">{pwm.freq()}</span></p>
            <input type="range" id="fSlider" min="1" max="20000" value="{pwm.freq()}" 
                oninput="update('freq', this.value)">

            <br><br>
            <button onclick="stopMotor()" style="background-color:red; color:white; padding:20px; width:100%; font-size:20px; border-radius:10px;">
                STOP MOTOR
            </button>

            <script>
            function update(type, val) {{
                document.getElementById(type == 'speed' ? 'sVal' : 'fVal').innerText = val;
                fetch('/update?' + type + '=' + val);
            }}

            function stopMotor() {{
                document.getElementById('sSlider').value = 0;
                document.getElementById('sVal').innerText = 0;
                fetch('/update?speed=0');
            }}
            </script>
            """
            
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body style='font-family:sans-serif; padding:20px;'>" + body + "</body></html>"
            conn.send(response.encode())
        
        conn.close()
    except Exception as e:
        print("Error:", e)
        if 'conn' in locals(): conn.close()
