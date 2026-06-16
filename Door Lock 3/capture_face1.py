import cv2
import requests
import numpy as np
import os

# ==========================================
# CONFIGURATION
# ==========================================
URL = "http://10.77.174.222/" 
MAX_SAMPLES = 50  # Number of face images to capture
# ==========================================

# Create a directory to store the face data if it doesn't exist
if not os.path.exists('dataset'):
    os.makedirs('dataset')

# Initialize the face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Get the user ID
face_id = input('\nEnter a numeric ID for this person (e.g., 1, 2) and press <return> ==>  ')
print("\n[INFO] Initializing face capture. Look at the camera and wait...")

# Open the stream
try:
    stream = requests.get(URL, stream=True, timeout=5)
    if stream.status_code != 200:
        print(f"[ERROR] Server returned code: {stream.status_code}")
        exit()
except Exception as e:
    print(f"[FAILURE] Could not connect: {e}")
    exit()

bytes_buffer = b''
sample_count = 0

# Process the stream
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

                    for (x, y, w, h) in faces:
                        # Draw a rectangle around the face for visual feedback
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)     
                        sample_count += 1

                        # Save the captured face into the datasets folder
                        # We slice the image array to save only the pixels inside the bounding box
                        cv2.imwrite(f"dataset/User.{face_id}.{sample_count}.jpg", gray[y:y+h, x:x+w])
                        
                        # Briefly pause to allow the person to move slightly between captures
                        cv2.waitKey(100)

                    cv2.imshow('Face Data Collection', frame)

        else:
            bytes_buffer = bytes_buffer[a:]
            
    # Break the loop when we have enough samples or if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break
    elif sample_count >= MAX_SAMPLES:
        break

print(f"\n[INFO] Successfully captured {sample_count} faces. Exiting Program.")
cv2.destroyAllWindows()