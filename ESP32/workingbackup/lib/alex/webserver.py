import socket

class WebServerHandler:
    def __init__(self):

        # Set up the web server
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self.server = socket.socket()
        self.server.bind(addr)
        self.server.listen(1)
        print('Listening on', addr)

    def serve_html(self,last_temperature = None, last_humidity = None):
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>DHT11 Sensor</title></head>
        <body>
            <h1>ESP32 DHT11 Sensor Readings</h1>
            <p><strong>Temperature:</strong> {last_temperature if last_temperature is not None else "Reading..."}°C</p>
            <p><strong>Humidity:</strong> {last_humidity if last_humidity is not None else "Reading..."}%</p>
        </body>
        </html>
        """
        return html
    
    def getServer(self):
        return self.server
