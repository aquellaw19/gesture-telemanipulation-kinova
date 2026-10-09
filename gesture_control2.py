import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions.hands import HandLandmark
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
from relaxed_ik_ros2.msg import EEPoseGoals, EEVelGoals

def is_fingers_curled(hand_landmarks):
   for tip in range(8,21,4):
      mcp = tip-3
      if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[mcp].y:
         return False
   return True

def is_fist(hand_landmarks, handedness):
    if not is_fingers_curled(hand_landmarks):
       return False 
    
    label = handedness.classification[0].label
    if label == 'Left':
       if hand_landmarks.landmark[4].x > hand_landmarks.landmark[2].x:
          return False
    elif label == 'Right':
       if hand_landmarks.landmark[4].x < hand_landmarks.landmark[2].x:
          return False
    return True

def is_open_palm(hand_landmarks,handedness):
    for tip in range(4,21,4):
        if tip == 4:
           mcp = tip-2
        else:
           mcp = tip-3
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[mcp].y:
            return False

    label = handedness.classification[0].label
    if label == 'Left':
       if hand_landmarks.landmark[4].x < hand_landmarks.landmark[0].x:
          return False
    elif label == 'Right':
       if hand_landmarks.landmark[4].x > hand_landmarks.landmark[0].x:
          return False
    return True

def is_thumbs_up(hand_landmarks,handedness):
#start/ activate  system
    if not is_fingers_curled(hand_landmarks):
      return False
    if hand_landmarks.landmark[4].y < hand_landmarks.landmark[0].y:
        label = handedness.classification[0].label
        if label == 'Left':
            if hand_landmarks.landmark[4].x > hand_landmarks.landmark[2].x:
                return True
        elif label == 'Right':
            if hand_landmarks.landmark[4].x < hand_landmarks.landmark[2].x:
                return True
    return False

def is_thumbs_down(hand_landmarks,handedness):
#pause system
    label = handedness.classification[0].label
    if hand_landmarks.landmark[4].y > hand_landmarks.landmark[0].y:
       if label == 'Left':
           if hand_landmarks.landmark[4].x > hand_landmarks.landmark[2].x:
              return True
       elif label == 'Right':
            if hand_landmarks.landmark[4].x < hand_landmarks.landmark[2].x:
               return True
    return False

def send_gripper_command(pos):
   """Subscribes to /gripper_position"""
   msg = Float64()
   msg.data = pos
   gripper_pub.publish(msg)


def send_ik_command(delta_x, delta_y):
    if abs(delta_x) < 0.01 and abs(delta_y) < 0.01:
       return
    scale = 0.5
    msg = EEVelGoals()
    twist = Twist()
    twist.linear.x = -delta_x * scale
    twist.linear.y = 0.0
    twist.linear.z = -delta_y * scale

    twist.angular.x = 0.0
    twist.angular.y = 0.0
    twist.angular.z = 0.0

    tolerance = Twist()
    tolerance.linear.x = 0.0
    tolerance.linear.y = 0.0
    tolerance.linear.z = 0.0

    tolerance.angular.x = 0.0
    tolerance.angular.y = 0.0
    tolerance.angular.z = 0.0

    msg.ee_vels.append(twist)
    msg.tolerances.append(tolerance)

    publisher.publish(msg)


is_active = False
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)
prev_wrist_x = None
prev_wrist_y= None

rclpy.init()
node = rclpy.create_node('gesture_control_node')
publisher = node.create_publisher(EEVelGoals, '/relaxed_ik/ee_vel_goals', 10)
gripper_pub = node.create_publisher(Float64, '/gripper_position', 10)

with mp_hands.Hands(min_detection_confidence=0.7) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        rclpy.spin_once(node, timeout_sec=0)
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                if prev_wrist_x is not None and  prev_wrist_y is not None: 
                   delta_x = hand_landmarks.landmark[0].x - prev_wrist_x
                   delta_y = hand_landmarks.landmark[0].y - prev_wrist_y
 
                if is_thumbs_up(hand_landmarks,handedness):
                   is_active = True
                   cv2.putText(frame, 'Thumbs Up - Active', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,255,0),2)
                elif is_active:
                     if prev_wrist_x is not None and prev_wrist_y is not None:
                        send_ik_command(delta_x, delta_y)
                     if is_open_palm(hand_landmarks, handedness):
                        send_gripper_command(0.0)
                        cv2.putText(frame, 'Open Palm', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,255,0),2)
                     elif is_thumbs_down(hand_landmarks,handedness):
                        is_active = False
                        cv2.putText(frame, 'Thumbs Down - Paused', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,255,0),2)
                     elif is_fist(hand_landmarks,handedness):
                        send_gripper_command(0.8)
                        cv2.putText(frame, 'Fist', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,255),2)
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                prev_wrist_x=hand_landmarks.landmark[0].x
                prev_wrist_y=hand_landmarks.landmark[0].y
        cv2.imshow('Gesture Control', frame)
        if cv2.waitKey(1) & 0XFF == ord('q'):
            break
cap.release()
cv2.destroyAllWindows()
