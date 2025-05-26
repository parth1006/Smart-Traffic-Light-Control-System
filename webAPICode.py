import requests
import time
import base64
import os
from datetime import datetime

def initialize_firebase():
    """Initialize Firebase connection info."""
    # Firebase configuration - same as in your HTML file
    firebase_config = {
        "apiKey": "AIzaSyAPgYJabQqcaKKCn6rob3AZd54s4hAnaAs",
        "projectId": "sareesite-4aef4"
    }
    
    print("Firebase configuration loaded.")
    return firebase_config

def get_traffic_status(detected_count):
    """Determine traffic status based on detected count."""
    if detected_count < 4:
        return "LIGHT TRAFFIC", "\033[92m"  # Green color
    elif detected_count < 7:
        return "MEDIUM TRAFFIC", "\033[93m"  # Yellow color
    else:
        return "HEAVY TRAFFIC", "\033[91m"  # Red color

def fetch_latest_data(config):
    """Fetch the latest data from the IOT collection using Firebase REST API."""
    try:
        # Firestore REST API endpoint for querying collections
        base_url = f"https://firestore.googleapis.com/v1/projects/{config['projectId']}/databases/(default)/documents/IOT"
        
        # Make the request to get all documents
        response = requests.get(base_url, params={"key": config["apiKey"]})
        
        if response.status_code == 200:
            data = response.json()
            if 'documents' in data and data['documents']:
                # Sort documents by timestamp field (if it exists)
                sorted_docs = sorted(
                    data['documents'], 
                    key=lambda doc: doc.get('fields', {}).get('timestamp', {}).get('stringValue', ''),
                    reverse=True  # Most recent first
                )
                
                # Get the most recent document
                if sorted_docs:
                    doc_data = parse_firestore_document(sorted_docs[0])
                    return doc_data
            
            print("No documents found in collection!")
            return None
        else:
            print(f"Error fetching data: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error getting documents: {e}")
        return None

def parse_firestore_document(doc):
    """Parse Firestore document from REST API format to a simple dict."""
    result = {}
    
    if 'fields' in doc:
        for key, value in doc['fields'].items():
            # Extract the value based on its type
            for type_key, actual_value in value.items():
                if type_key == 'stringValue':
                    result[key] = actual_value
                elif type_key == 'integerValue':
                    result[key] = int(actual_value)
                elif type_key == 'doubleValue':
                    result[key] = float(actual_value)
                elif type_key == 'booleanValue':
                    result[key] = bool(actual_value)
                elif type_key == 'timestampValue':
                    result[key] = actual_value
                elif type_key == 'arrayValue':
                    # Handle array values if needed
                    result[key] = [parse_firestore_value(item) for item in actual_value.get('values', [])]
                elif type_key == 'mapValue':
                    # Handle nested maps if needed
                    if 'fields' in actual_value:
                        result[key] = {k: parse_firestore_value(v) for k, v in actual_value['fields'].items()}
                    else:
                        result[key] = {}
    
    return result

def parse_firestore_value(value_dict):
    """Helper function to parse Firestore values."""
    for type_key, actual_value in value_dict.items():
        if type_key == 'stringValue':
            return actual_value
        elif type_key == 'integerValue':
            return int(actual_value)
        elif type_key == 'doubleValue':
            return float(actual_value)
        elif type_key == 'booleanValue':
            return bool(actual_value)
        elif type_key == 'timestampValue':
            return actual_value
    return None


def display_data(data):
    """Display the IoT data in the terminal."""
    if not data:
        return
    
    # Clear terminal screen (works on both Windows and Unix-like systems)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # ANSI color codes for formatting
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Print header
    print(f"{BOLD}===== IoT Data Viewer ====={RESET}")
    print(f"{BOLD}Last Updated: {datetime.now().strftime('%H:%M:%S')}{RESET}")
    print("=" * 30)
    
    # Print device information
    print(f"{BOLD}Device Information:{RESET}")
    print(f"  Device ID: {data.get('device_id', 'N/A')}")
    print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
    print(f"  Detected Count: {data.get('detected_count', 'N/A')}")
    print(f"  Has Detections: {data.get('has_detections', 'N/A')}")
    print(f"  Image Name: {data.get('image_name', 'N/A')}")
    print("-" * 30)
    
    # Print traffic status
    if 'detected_count' in data:
        traffic_text, color = get_traffic_status(data['detected_count'])
        print(f"{BOLD}Traffic Status:{RESET} {color}{traffic_text}{RESET}")
    else:
        print(f"{BOLD}Traffic Status:{RESET} No detection data available")
    
    # Handle image if available
    if 'imagebase64' in data and data['imagebase64']:
        image_path = "latest_iot_image.jpg"
        if save_image(data['imagebase64'], image_path):
            print(f"\nImage saved as: {image_path}")
    else:
        print("\nNo image data available")
    
    print("=" * 30)

def main():
    """Main function to run the IoT data viewer."""
    print("Initializing IoT Data Terminal Viewer...")
    
    # Initialize Firebase configuration
    firebase_config = initialize_firebase()
    
    try:
        while True:
            # Fetch and display data
            data = fetch_latest_data(firebase_config)
            display_data(data)
            
            # Wait for 1 second before refreshing data
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()