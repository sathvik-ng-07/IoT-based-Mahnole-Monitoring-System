from flask import Flask, jsonify
import serial
import serial.tools.list_ports
import time
import threading

app = Flask(__name__)

# Global variable to hold the latest Arduino data
latest_data = {}

# Function to find Arduino port
def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if 'Arduino' in p.description or 'CH340' in p.description or 'USB-SERIAL' in p.description:
            return p.device
    return None

# Function to read data from Arduino
def read_arduino_data():
    port = find_arduino_port()
    if port is None:
        print("⚠️ Arduino not found. Is it connected?")
        return
    
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"📥 {line}")
                # Update the global variable with the latest data
                latest_data['sensor_data'] = line
    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")

# Start the Arduino data reading in a separate thread
thread = threading.Thread(target=read_arduino_data)
thread.daemon = True  # Daemonize the thread to exit when the main program exits
thread.start()

# Route to get the latest sensor data
@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(latest_data)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)

