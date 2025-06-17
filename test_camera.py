# test_camera.py
import cv2

print("Attempting to open camera...")
cap = cv2.VideoCapture(0) # Coba ganti angka 0 ini dengan 1, -1 jika perlu

if not cap.isOpened():
    print("Error: Could not open camera. Please check if camera is in use or drivers are installed.")
else:
    print("Camera opened successfully! Trying to read frame...")
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to grab frame from camera.")
    else:
        print("Successfully grabbed a frame! Displaying for 5 seconds...")
        cv2.imshow('Camera Test', frame)
        cv2.waitKey(5000) # Tampilkan frame selama 5 detik
        cv2.destroyAllWindows()
        print("Test finished.")
cap.release()