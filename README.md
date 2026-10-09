# Human Gesture-Based Robot Telemanipulation
Real-time hand gesture recognition (MediaPipe + OpenCV) for teleoperating a Kinova Gen3 arm in simulation using ROS2 and RelaxedIK.

## Demo

## Gesture Mapping

| Gesture | Action | Logic |
|---------|--------|-------|
| Open Palm | Open gripper / Move arm | Fingertips (index–pinky) above base knuckles; thumb tip to the right of wrist (left hand) |
| Fist | Close gripper / Move arm | Fingertips (index–pinky) below base knuckles; thumb tucked |
| Thumbs Up | Activate system | Fingers curled, thumb tip above wrist, handedness-aware X check |
| Thumbs Down | Pause system | Thumb tip below wrist, handedness-aware X check |

Arm movement runs continuously when the system is active, based on wrist landmark position. Gestures trigger gripper commands.

## System Architecture

## Dependencies

## Installation & Setup

## Usage

## Known Limitations

## Acknowledgements
