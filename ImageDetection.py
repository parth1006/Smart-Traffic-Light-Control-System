import requests
import cv2
import numpy as np
import os
import time
import threading
from datetime import datetime
from io import BytesIO
from ultralytics import YOLO
import matplotlib.pyplot as plt
import base64
# ESP32-CAM Video Stream URL
ESP32_URL = "http://172.20.10.3:81/stream?drop=0"

load_dotenv(dotenv_path='key.env')
# Directory to save images
SAVE_DIR = "captured_images"
os.makedirs(SAVE_DIR, exist_ok=True)

# Your Firebase Configuration
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID")
}
# Load YOLOv8 model
model = YOLO('yolov10m.pt')

# Firebase Firestore REST API URL (using Firestore rather than Realtime Database)
# For Firestore REST API, we need to use a different endpoint format
FIREBASE_FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/IOT"
# Global variables
latest_frame = None
frame_lock = threading.Lock()
running = True

def preprocess_image(image):
    # Denoise image to reduce compression artifacts
    denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

    # Sharpen the image to enhance edges and features
    sharpening_kernel = np.array([[-1, -1, -1],
                                  [-1, 9, -1],
                                  [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, sharpening_kernel)

    # Upscale the image to help YOLO detect small objects
    scale_percent = 150  # Increase resolution by 1.5x
    width = int(sharpened.shape[1] * scale_percent / 100)
    height = int(sharpened.shape[0] * scale_percent / 100)
    upscaled = cv2.resize(sharpened, (width, height), interpolation=cv2.INTER_CUBIC)

    return upscaled

def detect_objects(image_path):
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read image from {image_path}")
        return []

    # Convert and preprocess
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_rgb = preprocess_image(image_rgb)

    # Run inference
    results = model(image_rgb)
    detections = results[0]

    # Prepare annotated image
    annotated_image = image_rgb.copy()
    detected_objects = []
    detection_results = []

    for detection in detections.boxes.data.tolist():
        x1, y1, x2, y2, confidence, class_id = detection

        if confidence < 0.01:  # Lowered threshold for noisy input
            continue

        x1, y1, x2, y2, class_id = int(x1), int(y1), int(x2), int(y2), int(class_id)
        class_name = detections.names[class_id]
        detected_objects.append(class_name)
        
        # Add detection details to results
        detection_results.append({
            "class": class_name,
            "confidence": float(confidence),
            "bbox": [int(x1), int(y1), int(x2), int(y2)]
        })

        # Draw box and label
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{class_name}: {confidence:.2f}"
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(annotated_image, (x1, y1 - label_height - 10), (x1 + label_width, y1), (0, 255, 0), -1)
        cv2.putText(annotated_image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

    # Print results
    print(f"Number of objects detected: {len(detected_objects)}")
    if detected_objects:
        print("Objects detected:")
        for i, obj in enumerate(detected_objects, 1):
            print(f"{i}. {obj}")
    else:
        print("No objects detected")

    # Display original and annotated image side-by-side
    # plt.figure(figsize=(12, 6))

    # plt.subplot(1, 2, 1)
    # plt.title("Raw Image")
    # plt.imshow(image_rgb)
    # plt.axis('off')

    # plt.subplot(1, 2, 2)
    # plt.title("Detected Objects")
    # plt.imshow(annotated_image)
    # plt.axis('off')

    # plt.tight_layout()
    # plt.show()
    # plt.close()
    
    return detection_results

# Try a different approach using a simple Firebase REST API endpoint
def post_to_firebase_simple(detection_results, image_path):
    """A simpler approach to post to Firebase"""
    # Create a simple data structure
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    image_name = os.path.basename(image_path)
    with open(image_path, "rb") as image_file:
            # Encode the binary data to base64
        encoded_string = base64.b64encode(image_file.read())
            
            # Convert bytes to string for easier handling
        base64_string = encoded_string.decode('utf-8')
    # Simplified data structure
    data = {
        "timestamp": timestamp,
        "image_name": image_name,
        "device_id": "ESP32-CAM-01",
        "has_detections": len(detection_results) > 0,
        "detected_count": len(detection_results),
        "imagebase64":base64_string
    }
    
    # Add detection classes if any
    if detection_results:
        data["classes"] = list(set([item["class"] for item in detection_results]))
    
    # Try Firestore API format
    firestore_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/IOT"
    
    # Convert to Firestore format
    firestore_fields = {}
    for key, value in data.items():
        if key == "has_detections":
            firestore_fields[key] = {"booleanValue": value}
        elif key == "detected_count":
            firestore_fields[key] = {"integerValue": str(value)}
        elif key == "classes" and value:
            array_items = [{"stringValue": x} for x in value]
            firestore_fields[key] = {"arrayValue": {"values": array_items}}
        else:
            firestore_fields[key] = {"stringValue": str(value)}
    
    firestore_data = {"fields": firestore_fields}
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(firestore_url, json=firestore_data, headers=headers)
        print(f"Firestore API response: {response.status_code} - {response.text[:100]}...")
        
        
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error in simple Firebase post: {e}")
        return False

def stream_reader():
    """Thread function to continuously read from the stream"""
    global latest_frame, running
    
    # Set a very short timeout to prevent blocking
    session = requests.Session()
    
    try:
        response = session.get(ESP32_URL, stream=True, timeout=5)
        print(f"Connection status: {response.status_code}")
        
        if response.status_code != 200:
            print("Failed to connect to camera")
            running = False
            return
            
        buffer = BytesIO()
        
        for chunk in response.iter_content(chunk_size=1024):
            if not running:
                break
                
            buffer.write(chunk)
            buffer_data = buffer.getvalue()
            
            # Find the most recent complete JPEG frame
            last_start = buffer_data.rfind(b'\xff\xd8')
            if last_start != -1:
                last_end = buffer_data.find(b'\xff\xd9', last_start)
                if last_end != -1:
                    # Extract the latest complete frame
                    jpg = buffer_data[last_start:last_end+2]
                    
                    # Decode and store the frame
                    try:
                        nparr = np.frombuffer(jpg, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        if img is not None:
                            with frame_lock:
                                latest_frame = img
                    except Exception as e:
                        print(f"Error decoding frame: {e}")
                    
                    # Reset buffer to discard all processed data
                    # Only keep data after the last frame end
                    new_buffer = BytesIO()
                    new_buffer.write(buffer_data[last_end+2:])
                    buffer = new_buffer
    
    except Exception as e:
        print(f"Stream reader error: {e}")
    finally:
        running = False
        session.close()

def main():
    global latest_frame, running
    
    # Start the stream reader thread
    reader_thread = threading.Thread(target=stream_reader)
    reader_thread.daemon = True
    reader_thread.start()
    
    frame_count = 0
    
    # Give the reader thread a moment to start and get initial frames
    time.sleep(1)
    
    capture_interval = 0  # Capture every 2 seconds
    
    try:
        print("Automatic frame capture started. Press Ctrl+C to stop.")
        while running:
            # Get the latest frame
            current_frame = None
            with frame_lock:
                if latest_frame is not None:
                    current_frame = latest_frame.copy()
            
            if current_frame is not None:
                # Save the image
                img_filename = os.path.join(SAVE_DIR, f"frame_{frame_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                cv2.imwrite(img_filename, current_frame)
                print(f"Saved latest frame: {img_filename}")
                detection_results = detect_objects(img_filename)
                success = post_to_firebase_simple(detection_results, img_filename)
                os.remove(img_filename)
                print(f"Processed, {'uploaded to Firebase' if success else 'failed to upload'}, and deleted image.")
                frame_count += 1
            else:
                print("No frame available yet")
            
            # Wait for the next capture
            time.sleep(capture_interval)
    
    except KeyboardInterrupt:
        print("\nCapture interrupted by user")
    except Exception as e:
        print(f"Error in main thread: {e}")
    finally:
        running = False
        reader_thread.join(timeout=2)
        print("Image capture and processing completed!")

if __name__ == "__main__":
    main()
