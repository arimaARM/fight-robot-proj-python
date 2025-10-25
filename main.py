import network 
import socket 
from time import sleep 
import machine 
from machine import Pin

ssid = 'Proximus-Home-61F8'
password = 'wfkeyna463xne'

mot_A1_Forward = Pin(6, Pin.OUT)
mot_A2_Back = Pin (7, Pin.OUT)
mot_B1_Forward = Pin(8, Pin.OUT)
mot_B2_Back = Pin (9, Pin.OUT)

def move_forward():

    mot_A1_Forward(1)
    mot_B1_Forward(1)
    mot_A2_Back(0)
    mot_B2_Back(0)

def move_backward():

    mot_A2_Back(1)
    mot_B2_Back(1)
    mot_A1_Forward(0)
    mot_B1_Forward(0)

def move_left():

    mot_A1_Forward(1)
    mot_B2_Back(1)
    mot_B1_Forward(0)
    mot_A2_Back(0)

def move_right():
    
    mot_B1_Forward(1)
    mot_A2_Back(1)
    mot_A1_Forward(0)
    mot_B2_Back(0)

def move_stop():
    mot_A1_Forward(0)
    mot_A2_Back(0)
    mot_B1_Forward(0)
    mot_B2_Back(0)

def connect():

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print ('Waiting for connetcion ...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}') 
    return ip

def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)   
    connection.listen(1)
    return connection 

def webpage():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Joystick Control</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f0f0f0;
        }
        h1 { color: #333; }
        #joystickContainer {
            position: relative;
            width: 300px;
            height: 300px;
            margin: 50px auto;
            background-color: #ddd;
            border-radius: 50%;
            touch-action: none;
        }
        #joystick {
            position: absolute;
            width: 100px;
            height: 100px;
            background-color: #4CAF50;
            border-radius: 50%;
            left: 100px;
            top: 100px;
            cursor: pointer;
            touch-action: none;
        }
    </style>
</head>
<body>
    <h1>Joystick Control</h1>
    <div id="joystickContainer">
        <div id="joystick"></div>
    </div>
    <script>
        const joystick = document.getElementById('joystick');
        const container = document.getElementById('joystickContainer');
        const centerX = container.offsetWidth/2 - joystick.offsetWidth/2;
        const centerY = container.offsetHeight/2 - joystick.offsetHeight/2;
        joystick.style.left = centerX + 'px';
        joystick.style.top = centerY + 'px';

        let dragging = false;

        function sendCommand(cmd) {
            fetch('/' + cmd);
        }

        function moveJoystick(x, y) {
            const rect = container.getBoundingClientRect();
            let dx = x - rect.left - joystick.offsetWidth/2;
            let dy = y - rect.top - joystick.offsetHeight/2;

            const maxDist = container.offsetWidth/2 - joystick.offsetWidth/2;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if(dist > maxDist){
                dx = dx*maxDist/dist;
                dy = dy*maxDist/dist;
            }

            joystick.style.left = (centerX + dx) + 'px';
            joystick.style.top = (centerY + dy) + 'px';

            // Определяем направление
            if(Math.abs(dx) < 20 && dy < -20) sendCommand('forward');
            else if(Math.abs(dx) < 20 && dy > 20) sendCommand('backward');
            else if(dx < -20 && Math.abs(dy) < 20) sendCommand('left');
            else if(dx > 20 && Math.abs(dy) < 20) sendCommand('right');
            else sendCommand('stop');
        }

        joystick.addEventListener('mousedown', e => dragging = true);
        window.addEventListener('mouseup', e => {
            dragging = false;
            joystick.style.left = centerX + 'px';
            joystick.style.top = centerY + 'px';
            sendCommand('stop');
        });
        window.addEventListener('mousemove', e => { if(dragging) moveJoystick(e.clientX, e.clientY); });

        // Сенсорные события
        joystick.addEventListener('touchstart', e => { dragging = true; e.preventDefault(); });
        window.addEventListener('touchend', e => { 
            dragging = false; 
            joystick.style.left = centerX + 'px';
            joystick.style.top = centerY + 'px';
            sendCommand('stop');
        });
        window.addEventListener('touchmove', e => {
            if(dragging){
                moveJoystick(e.touches[0].clientX, e.touches[0].clientY);
                e.preventDefault();
            }
        });
    </script>
</body>
</html>
"""
    return html


def serve(connection):
    while True:
        client, addr = connection.accept()
        print('Client connected from', addr)
        request = client.recv(1024).decode()
        print('Request:', request)

        try:
            path = request.split()[1]
        except IndexError:
            path = '/'

        if path.startswith('/forward'):
            move_forward()
        elif path.startswith('/backward'):
            move_backward()
        elif path.startswith('/left'):
            move_left()
        elif path.startswith('/right'):
            move_right()
        elif path.startswith('/stop'):
            print("Stop motors")

        response = webpage()
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: text/html\n')
        client.send('Connection: close\n\n')
        client.sendall(response)
        client.close()

try: 
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    machine.reset()
