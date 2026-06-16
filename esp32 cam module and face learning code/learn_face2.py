import cv2
import numpy as np
import os

# ==========================================
# CONFIGURATION
# ==========================================
# Path to the dataset folder created in Phase 1
DATASET_PATH = 'dataset'
# ==========================================

print("\n[INFO] Initializing training process. Please wait...")

# Create the LBPH Face Recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()

def get_images_and_labels(path):
    """
    Reads the images from the dataset folder and extracts the face ID
    from the filename (e.g., User.1.25.jpg -> ID: 1).
    """
    # Get the paths to all files in the dataset directory
    image_paths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jpg')]
    
    faces = []
    ids = []
    
    for image_path in image_paths:
        # Read the image and ensure it is in grayscale
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            continue
            
        # Extract the ID from the filename
        # Filename format: User.{id}.{count}.jpg
        file_name = os.path.split(image_path)[-1]
        face_id = int(file_name.split('.')[1])
        
        faces.append(img)
        ids.append(face_id)
        
    return faces, ids

# Gather the data
faces, ids = get_images_and_labels(DATASET_PATH)

print(f"[INFO] Found {len(faces)} images for {len(np.unique(ids))} distinct user(s). Training model...")

# Train the recognizer model on the extracted faces and IDs
recognizer.train(faces, np.array(ids))

# Create a directory to store the trained model if it doesn't exist
if not os.path.exists('trainer'):
    os.makedirs('trainer')

# Save the trained model to a YAML file
recognizer.write('trainer/trainer.yml')

print(f"\n[SUCCESS] Model trained and saved to 'trainer/trainer.yml'. Exiting Program.")