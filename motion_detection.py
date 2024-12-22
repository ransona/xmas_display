import cv2
import numpy as np
import time

def detect_motion(video_capture, area_threshold):
    """
    Detects motion in video from a webcam.

    Args:
    - video_capture (cv2.VideoCapture): The video capture object.
    - area_threshold (int): The minimum area size for motion to be considered significant.

    Returns:
    - bool: True if motion is detected, False otherwise.
    """
    # Read two frames, with a 1 second pause in between
    ret, frame1 = video_capture.read()
    time.sleep(1)
    ret, frame2 = video_capture.read()

    if not ret:
        return False

    # Calculate the absolute difference between the two frames
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Check if any contours are larger than the area threshold
    for contour in contours:
        if cv2.contourArea(contour) > area_threshold:
            return True

    return False
