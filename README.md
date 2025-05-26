# Smart-Traffic-Light-Control-System
# 🚦 Smart Traffic Signal Control System (IoT + YOLOv8 + ESP32)

A real-time adaptive traffic light control system that uses an **ESP32-CAM**, **YOLOv8**, and Firebase to dynamically manage signal durations based on vehicle density. This project was built as part of the *IoT Architectures and Protocols* course at VIT Vellore.

---

## 📌 Project Overview

Urban traffic signals often operate on static timers, causing unnecessary delays and inefficiencies. This system introduces an intelligent solution using IoT and computer vision that:

- Captures real-time traffic using **ESP32-CAM**
- Detects and counts vehicles using **YOLOv8**
- Adjusts green light durations using **ESP32**
- Displays traffic conditions on an **LCD screen** and a **terminal dashboard**
- Stores detection results and images on **Firebase Firestore**

---

## 🎯 Features

- 🧠 **YOLOv8 Vehicle Detection**  
  Real-time object detection with preprocessed and enhanced frames

- 🚦 **Dynamic Traffic Signal Logic**  
  ESP32 dynamically sets green light duration based on detected traffic

- 📟 **LCD Display Integration**  
  Live countdown timer for the green light phase

- 🌐 **Firebase Firestore Integration**  
  Uploads detection metadata and images (base64) for centralized access

- 🖥️ **Terminal-Based Web App**  
  Python dashboard fetches and displays the latest traffic data and image

---

## 🛠️ Tech Stack

**Hardware:**  
- ESP32-CAM  
- ESP32 Microcontroller  
- LCD Display (I2C)  
- TTL to USB Converter

**Software:**  
- Python, OpenCV, YOLOv8 (`ultralytics`)  
- Arduino IDE  
- Firebase Firestore (REST API)  
- Matplotlib, Base64  
- Hugging Face API (planned for future)

---

## 📂 Project Structure

├── ImageDetection.py # YOLOv8 object detection and Firebase integration
├── webAPICode.py # Terminal dashboard for live traffic status
├── realTimeVideoCapture.ino # ESP32-CAM firmware to stream real-time video
├── lcdIntegration.ino # ESP32 logic for signal control and LCD display
├── Initial Project Report.pdf# Early planning and design documentation
├── review.pdf # Literature review of IoT-based traffic systems
├── db3acef7-7098-4f54-84b9-f44980e6e3a3.jpg # Setup image
└── README.md


---

## 🚦 System Workflow

1. **ESP32-CAM** streams live video of traffic lanes.
2. Python script (`ImageDetection.py`) captures and preprocesses frames.
3. **YOLOv8** detects vehicles, calculates traffic density.
4. Detection data is sent to **Firebase Firestore** and displayed via:
   - ESP32-controlled **LCD**
   - Python-based **terminal viewer** (`webAPICode.py`)
5. Traffic signal timing is adjusted dynamically based on density.

---

## 🖼️ Prototype Setup

Here’s our working prototype:

<img src="./db3acef7-7098-4f54-84b9-f44980e6e3a3.jpg" alt="Smart Traffic System Setup" width="600"/>

- ESP32-CAM mounted above the test track captures video
- ESP32 drives the signal logic
- LCD displays remaining green time

---

## ⚙️ Setup Instructions

### 1. Flash ESP32-CAM
- Open `realTimeVideoCapture.ino` in Arduino IDE
- Connect to your Wi-Fi credentials
- Flash it onto ESP32-CAM

### 2. Flash ESP32 Controller
- Upload `lcdIntegration.ino` to ESP32
- Connect LCD display via I2C

### 3. Python Environment

# Or manually install: ultralytics, opencv-python, matplotlib, requests

📚 Project Documentation
📘 Initial Project Report: Planning, objectives, system design

📄 Literature Review: In-depth research on IoT-based traffic control systems
