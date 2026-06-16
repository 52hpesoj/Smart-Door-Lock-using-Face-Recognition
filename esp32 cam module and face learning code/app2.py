from flask import Flask, render_template, Response, jsonify
import cv2
import requests
import numpy as np
import time

app = Flask(__name__)

# ==========================================
# CONFIGURATION - THE TWO BOARDS
# ==========================================
# 1. The Eye: Where the video comes from
CAMERA_URL = "http://10.77.174.222/" 

# 2. The Hands: Where the LCD, LEDs, and Buzzer are (Update this!)
CONTROLLER_URL = "http://10.77.174.239/" 

NAMES = ['Unknown','Joseph'] 

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

door_state = {"status": "locked", "user": "Unknown"}
cooldown_until = 0  
# ==========================================

def generate_frames():
    global door_state, cooldown_until
    door_unlock_timer = 0
    try:
        # Pull video from the Camera
        stream = requests.get(CAMERA_URL, stream=True, timeout=5)
    except Exception as e:
        print(f"[FAILURE] Could not connect to Camera: {e}")
        return

    bytes_buffer = b''
    last_action = "none"

    for chunk in stream.iter_content(chunk_size=1024):
        bytes_buffer += chunk
        a = bytes_buffer.find(b'\xff\xd8')
        b = bytes_buffer.find(b'\xff\xd9')
        
        if a != -1 and b != -1:
            if a < b:
                jpg = bytes_buffer[a:b+2]
                bytes_buffer = bytes_buffer[b+2:] 
                
                if len(jpg) > 0:
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        current_time = time.time()
                        
                        if current_time < cooldown_until:
                            time_left = int(cooldown_until - current_time) + 1
                            cv2.putText(frame, f"COOLDOWN: {time_left}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        else:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
                            
                            face_recognized = False
                            face_detected = len(faces) > 0

                            for (x, y, w, h) in faces:
                                id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                                
                                if confidence < 80:
                                    name = NAMES[id] if id < len(NAMES) else "Unknown"
                                    color = (0, 255, 0) 
                                    face_recognized = True
                                    
                                    door_state["status"] = "unlocked"
                                    door_state["user"] = name
                                else:
                                    name = "Unknown"
                                    color = (0, 0, 255) 
                                    
                                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                                cv2.putText(frame, str(name), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                        
                            # ==================================================
                            # UPDATED HARDWARE CONTROL LOGIC
                            # ==================================================
                            current_time = time.time()
                            
                            # ONLY process new commands if the door isn't currently unlocked
                            if current_time > door_unlock_timer:
                                
                                if face_recognized and last_action != "granted":
                                    try: requests.get(f"{CONTROLLER_URL}granted?name={name}", timeout=3)
                                    except: pass
                                    last_action = "granted"
                                    # FREEZE the lock open for 5 seconds!
                                    door_unlock_timer = current_time + 5 
                                    
                                elif face_detected and not face_recognized and last_action != "denied":
                                    try: requests.get(f"{CONTROLLER_URL}denied", timeout=3)
                                    except: pass
                                    last_action = "denied"
                                    
                                elif not face_detected:
                                    last_action = "none" 
                            # ================================================== 

                        ret, buffer = cv2.imencode('.jpg', frame)
                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                bytes_buffer = bytes_buffer[a:]

# --- WEB ROUTES ---

@app.route('/')
def index():
    return render_template('standby.html') # The new sleeping page

@app.route('/scan')
def scan():
    return render_template('scanning.html') # The actual camera page

@app.route('/recognized')
def recognized():
    return render_template('recognized.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify(door_state)

@app.route('/lock')
def lock():
    global door_state, cooldown_until
    door_state["status"] = "locked"
    door_state["user"] = "Unknown"
    cooldown_until = time.time() + 3
    
    # Send the lock command to the Door Controller
    try: 
        requests.get(f"{CONTROLLER_URL}lock", timeout=1)
    except: 
        pass
        
    return jsonify({"result": "success"})

@app.route('/check_doorbell')
def check_doorbell():
    try:
        # Python asks the ESP32 if the button is pressed
        response = requests.get(f"{CONTROLLER_URL}button", timeout=1)
        if response.text == "pressed":
            return jsonify({"ringing": True})
    except:
        pass
    
    return jsonify({"ringing": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)