from machine import Pin, PWM
import socket

# 1. Setup PWM
pwm_pin = Pin(33)
pwm = PWM(pwm_pin, freq=1000, duty_u16=0) # Start at 0 speed

# 2. Web Server Setup (Assuming you are already connected to WiFi)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        
        # Extract the path (e.g., "/speed?val=32768")
        request_line = request.splitlines()[0]
        path = request_line.split(" ")[1]

        # --- Speed Control Logic ---
        if "/speed" in path:
            try:
                # Extract value after "val="
                speed_str = path.split("val=")[1]
                duty_val = int(speed_str)
                
                # Constrain value between 0 and 65535
                duty_val = max(0, min(65535, duty_val))
                
                pwm.duty_u16(duty_val) # Apply the speed
                body = f"<h1>Speed set to: {duty_val}</h1>"
            except:
                body = "<h1>Error: Invalid Speed Value</h1>"
        
        elif path == "/temp":
            body = "<h1>Temperature Reading...</h1>" # Add your sensor code here
        else:
            # Default page with a Slider UI
            body = """
            <h1>Motor Control</h1>
            <p>Move the slider to change speed (0-65535):</p>
            <input type="range" min="0" max="65535" onchange="window.location.href='/speed?val=' + this.value">
            """

        # 3. Send Response
        HTTP_OK = "HTTP/1.1 200 OK\r\n"
        ContentType = "Content-Type: text/html\r\n\r\n"
        response = f"{HTTP_OK}{ContentType}<html><body>{body}</body></html>"
        
        conn.send(response.encode())
        conn.close()

    except Exception as e:
        print('Web server error:', e)
        if 'conn' in locals(): conn.close()
