# PuppyPi Navigation & HRI System

This folder contains three progressively enhanced Python scripts for controlling a PuppyPi robot dog using ROS2 (Nav2). The evolution demonstrates:

Basic CLI navigation – sending a goal coordinate from the command line.

Reliable navigation – automatic re‑localisation after each goal to prevent drift.

Voice + face recognition – wake‑word triggered navigation, then sit, face scan, and expressive actions (bow / box).


## Basic CLI Navigation (navigation_controller.py)
Goal: Move the robot to a given (x, y) coordinate on a pre‑built SLAM map.

### How it works:

Publishes a PoseStamped message to the /goal_pose topic.

Relies on the already running navigation stack (ros2 launch navigation navigation.launch.py map:=map_01).

No feedback, no re‑localisation.

### Limitations:

After one goal, the robot often loses localisation (drift) and won’t accept a second goal.

No way to know when the robot actually arrives



## Reliable Navigation (reliable_navigation.py)

### Improvements:

Subscribes to /move_base/status to detect when navigation succeeds.

Waits up to 60 seconds for goal completion.

Re‑localises automatically after each goal by publishing a high‑uncertainty pose on /initialpose, forcing AMCL to update.

Can be called sequentially from a script or the command line.



## Voice + Face Integration (voice_navigation.py)

Goal: A hands‑free, interactive experience – the user speaks a command, the robot navigates to a preset location, sits, scans for a face, and performs an expressive action.

Key components integrated:

Voice detector (commands_nomqtt.py)	to listen for wake word (e.g., “kitty”, "dog) then a command (“come here”).

Reliable navigation	Moves robot to a fixed point (e.g., (1.0, 1.0)).

Puppy action node (action.py)	Sends sit, bow, boxing action groups.

Face recognition uses OpenCV to identify a registered user from a trained model.


Flow:

1. Wait for wake word + command.

2. Navigate to the target coordinate.

3. Sit – robot sits down.

4. Scan for a face (up to 5 seconds).

5. If face recognised → perform bow action.

6. If no known face → perform boxing action.



## Prerequisites inside the PuppyPi Docker container
ROS2 Humble with Nav2 stack running

PuppyPi action groups available (the puppy_control node)

Python 3.10+

Required Python packages:
pip install pyaudio numpy vosk opencv-python opencv-contrib-python


## Running the System

### Terminal 1 – start the navigation stack (always do before running .py file)
ros2 launch navigation navigation.launch.py map:=map_01

### Terminal 2 – run the voice‑controlled script
python3 voice_navigation.py


### Expected behaviour
The script prints “Listening for wake words...”.

When you speak, you’ll see [Voice] ... and [Wake] Activated logs.

After the command, the robot drives to (1.0, 1.0), sits, scans, and then bows or boxes.



## Summary of Progress
navigation_controller.py – proof of concept to send a single goal once.

reliable_navigation.py – handling automatic start and reusability as well as re-localisation.

voice_navigation.py – integration with voice command, navigation, actions and face detection