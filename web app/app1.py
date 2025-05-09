from flask import Flask, jsonify, render_template
import serial.tools.list_ports
import time
import threading

# Create Flask application
app = Flask(__name__)

# Initial data structure
latest_data = {
    "temperature": None,
    "humidity": None,
    "distance": None,
    "gas": None,
    "raw_data": ["No data yet"]
}

# Variable to check if Arduino is connected
arduino_connected = False

# Track the last successful port
last_successful_port = None

def find_arduino_port():
    """Find Arduino serial port"""
    try:
        ports = list(serial.tools.list_ports.comports())
        print(f"Available ports: {[p.device for p in ports]}")
        
        for p in ports:
            print(f"Port {p.device}: {p.description}")
            # Common identifiers for Arduino boards
            if any(id in p.description for id in ['Arduino', 'CH340', 'USB-SERIAL', 'ttyACM', 'ttyUSB']):
                print(f"Found Arduino on port: {p.device}")
                return p.device
            
        # If we didn't find a port with a descriptive name, just use the first available port
        if ports:
            print(f"No Arduino identifier found. Using first available port: {ports[0].device}")
            return ports[0].device
        
        print("No COM ports found. Is the Arduino connected?")
        return None
    except Exception as e:
        print(f"Error finding Arduino port: {e}")
        return None

def read_arduino_data():
    """Read data from Arduino continuously"""
    global latest_data, arduino_connected
    
    reconnect_delay = 5  # Initial delay in seconds
    max_reconnect_delay = 30  # Maximum delay in seconds
    
    while True:
        port = find_arduino_port()
        if port is None:
            print(f"❌ Arduino not found. Retrying in {reconnect_delay} seconds...")
            arduino_connected = False
            time.sleep(reconnect_delay)
            # Exponential backoff with max cap
            reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
            continue
            
        try:
            # Reset reconnection delay on successful connection
            reconnect_delay = 5
            
            # Import pyserial directly
            import serial
            ser = serial.Serial(port, 9600, timeout=1)
            print(f"✅ Connected to port {port}")
            arduino_connected = True
            
            # Wait for Arduino to reset
            time.sleep(2)
            
            # Clear any buffered data
            ser.reset_input_buffer()
            
            buffer = []
            
            while True:
                # Check if serial port is still available
                if not ser.is_open:
                    print("❌ Serial port closed unexpectedly")
                    break
                    
                if ser.in_waiting:
                    try:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        print(f"Raw data received: '{line}'")
                        
                        # Check if we've reached the end of a data block
                        if "-----------------------------" in line:
                            print("🧾 End of data block")
                            
                            # Store the raw sensor data
                            latest_data['raw_data'] = buffer[:]
                            
                            # Parse specific sensor values
                            for data in buffer:
                                print(f"Parsing line: '{data}'")
                                
                                # More flexible temperature/humidity parsing
                                if "Temperature" in data:
                                    try:
                                        # Extract temperature and humidity from the same line
                                        parts = data.split(',')
                                        
                                        # Extract temperature
                                        if len(parts) > 0 and "Temperature" in parts[0]:
                                            temp_part = parts[0].split(":")
                                            if len(temp_part) > 1:
                                                latest_data['temperature'] = temp_part[1].strip()
                                                print(f"Extracted temperature: {latest_data['temperature']}")
                                        
                                        # Extract humidity
                                        if len(parts) > 1 and "Humidity" in parts[1]:
                                            humidity_part = parts[1].split(":")
                                            if len(humidity_part) > 1:
                                                latest_data['humidity'] = humidity_part[1].strip()
                                                print(f"Extracted humidity: {latest_data['humidity']}")
                                    except Exception as e:
                                        print(f"Error parsing temperature/humidity: {e}")
                                
                                elif "Distance" in data:
                                    try:
                                        dist_parts = data.split(":")
                                        if len(dist_parts) > 1:
                                            latest_data['distance'] = dist_parts[1].strip()
                                            print(f"Extracted distance: {latest_data['distance']}")
                                    except Exception as e:
                                        print(f"Error parsing distance: {e}")
                                        
                                elif "Gas" in data:
                                    try:
                                        gas_parts = data.split(":")
                                        if len(gas_parts) > 1:
                                            latest_data['gas'] = gas_parts[1].strip()
                                            print(f"Extracted gas: {latest_data['gas']}")
                                    except Exception as e:
                                        print(f"Error parsing gas: {e}")
                            
                            print(f"📊 Updated data: {latest_data}")
                            buffer = []  # Reset buffer
                        else:
                            buffer.append(line)
                    except Exception as e:
                        print(f"Error reading line: {e}")
                
                # Small delay to prevent CPU hogging
                time.sleep(0.01)
                
        except Exception as e:
            print(f"❌ Serial connection error: {e}")
            arduino_connected = False
            time.sleep(reconnect_delay)  # Wait before trying to reconnect
            # Exponential backoff with max cap
            reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to fetch the latest sensor data
@app.route('/data')
def data():
    # Add connection status to the response
    return_data = latest_data.copy()
    return_data['arduino_connected'] = arduino_connected
    return jsonify(return_data)

# Start the thread that reads from the Arduino
thread = threading.Thread(target=read_arduino_data)
thread.daemon = True
thread.start()

# Start the Flask app
if __name__ == '__main__':
    print("🚀 Starting Manhole Monitoring System")
    app.run(debug=True, use_reloader=False, threaded=True)