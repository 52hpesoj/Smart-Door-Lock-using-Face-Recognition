import cv2
import requests
import numpy as np

# ==========================================
# CONFIGURATION
# ==========================================
URL = "http://10.77.174.222/" 

# ID 0 is a placeholder for 'Unknown'. 
# ID 1 corresponds to the first set of dataset images.
NAMES = ['Unknown', 'Joseph','Joseph2'] 
# ==========================================

print(f"[INFO] Connecting to {URL} ...")

try:
    stream = requests.get(URL, stream=True, timeout=5)
    if stream.status_code == 200:
        print("   [SUCCESS] Connected to stream!")
    else:
        print(f"   [ERROR] Server returned code: {stream.status_code}")
        exit()
except Exception as e:
    print(f"   [FAILURE] Could not connect: {e}")
    exit()

# Load the face detector and the trained recognizer model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

bytes_buffer = b''
last_action = "none"

print("[INFO] AI Recognition Running... Press 'q' to quit.")

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
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

                    face_recognized = False

                    for (x, y, w, h) in faces:
                        # Ask the model to predict the ID of the face in the bounding box
                        id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                        
                        # A lower confidence number means a closer match. < 80 is a good threshold.
                        if confidence < 80:
                            name = NAMES[id] if id < len(NAMES) else "Unknown"
                            color = (0, 255, 0) # Green for authorized
                            face_recognized = True
                        else:
                            name = "Unknown"
                            color = (0, 0, 255) # Red for unauthorized
                            
                        # Draw the rectangle and the name label
                        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                        cv2.putText(frame, str(name), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        
                        # Display the confidence score as a percentage for debugging
                        match_percent = f"  {round(100 - confidence)}%"
                        cv2.putText(frame, match_percent, (x+5, y+h-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

                    # --- Hardware Control Logic ---
                    if face_recognized:
                        if last_action != "on":
                            print(f">> AUTHORIZED ({name}) -> LED ON")
                            try: requests.get(f"{URL}led_on", timeout=0.01)
                            except: pass
                            last_action = "on"
                    elif len(faces) > 0:
                        if last_action != "off":
                            print(">> UNKNOWN FACE -> LED OFF")
                            try: requests.get(f"{URL}led_off", timeout=0.01)
                            except: pass
                            last_action = "off"
                    else:
                        if last_action != "off":
                            print(">> No Face -> LED OFF")
                            try: requests.get(f"{URL}led_off", timeout=0.01)
                            except: pass
                            last_action = "off"
                    
                    cv2.imshow('ESP32 AI Recognition', frame)
                    
                    if cv2.waitKey(1) == ord('q'):
                        break
        else:
            bytes_buffer = bytes_buffer[a:]

cv2.destroyAllWindows()