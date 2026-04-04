#!/usr/bin/env python3
# reliable_navigation.py

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import String
import sys
import math
import time

class ReliableNavigator(Node):
    def __init__(self):
        super().__init__('reliable_navigator')
        
        # Publishers
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        
        # Subscribers
        self.status_sub = self.create_subscription(String, '/move_base/status', self.status_callback, 10)
        self.navigation_active = False
        self.last_status = None
        
        self.get_logger().info('Reliable Navigator ready')
    
    def status_callback(self, msg):
        """Track navigation completion"""
        self.last_status = msg.data
        if msg.data == 'success':
            self.get_logger().info('Navigation completed!')
            self.navigation_active = False
    
    def send_goal(self, x, y, theta=0.0):
        """Send navigation goal"""
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = 0.0
        
        q = self.euler_to_quaternion(0, 0, theta)
        msg.pose.orientation.x = q[0]
        msg.pose.orientation.y = q[1]
        msg.pose.orientation.z = q[2]
        msg.pose.orientation.w = q[3]
        
        self.goal_pub.publish(msg)
        self.navigation_active = True
        self.get_logger().info(f'Goal sent: ({x}, {y}, {theta:.2f})')
        
        # Wait for completion
        timeout = 60  # seconds
        start = time.time()
        while self.navigation_active and (time.time() - start) < timeout:
            rclpy.spin_once(self, timeout_sec=0.1)
        
        if self.navigation_active:
            self.get_logger().warn('Navigation timeout!')
            return False
        
        # CRITICAL: Re-localize after reaching goal
        self.relocalize()
        return True
    
    def relocalize(self):
        """Force AMCL to update robot position based on current laser scan"""
        self.get_logger().info('Re-localizing robot...')
        
        # Option 1: Force particle filter update by publishing a pose with high uncertainty
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        
        # Get current transform (or estimate)
        # This publishes a pose with high covariance, telling AMCL to re-evaluate
        msg.pose.covariance = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.5, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.5]
        
        self.initial_pose_pub.publish(msg)
        time.sleep(1)  # Give AMCL time to update
        
        self.get_logger().info('Re-localization complete')
    
    def reset_navigation(self):
        """Reset the navigation stack"""
        self.get_logger().info('Resetting navigation stack...')
        # Cancel any active goals
        self.navigation_active = False
        time.sleep(1)
    
    def euler_to_quaternion(self, roll, pitch, yaw):
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        return [
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy
        ]

def main():
    rclpy.init()
    navigator = ReliableNavigator()
    
    if len(sys.argv) < 3:
        print("Usage: reliable_navigation.py x y [theta]")
        print("Example: reliable_navigation.py 1.0 1.0")
        sys.exit(1)
    
    x = float(sys.argv[1])
    y = float(sys.argv[2])
    theta = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    
    success = navigator.send_goal(x, y, theta)
    
    if success:
        print(f"Successfully reached goal ({x}, {y})")
    else:
        print(f"Failed to reach goal ({x}, {y})")
    
    navigator.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

ï»¿
import json
import time
import numpy as np
from vosk import Model, KaldiRecognizer

class CommandDetector:
    def __init__(self, mqtt_client):
        self.mqtt = mqtt_client
        self.rate = 48000
        self.model = Model("model")
        self.rec = KaldiRecognizer(self.model, self.rate)
        self.listening_for_command = False

        self.wake_words = ["kitty", "cat", "kitten", "puppy", "dog", "doggy"]
        self.commands = {
            "fetch": ["fetch", "get", "bring", "grab"],
            "clean_up": ["clean", "sweep", "vacuum", "tidy"],
            "come_here": ["come", "here", "approach", "arrive"],
            "search": ["search", "find", "locate", "where"]
        }
        self.emergency_words = ["help", "emergency", "scream", "fire", "stop", "danger"]

    def process_next(self, chunk):
        chunk_int16 = (chunk * 32768).astype(np.int16).tobytes()
        if self.rec.AcceptWaveform(chunk_int16):
            result = json.loads(self.rec.Result())
            text = result.get('text', '').lower()
            if text:
                print(f"\n[Voice] {text}")

                # 1. Wake word
                if any(w in text for w in self.wake_words):
                    print("[Wake] Activated")
                    self.listening_for_command = True
                    for cmd, keywords in self.commands.items():
                        if any(kw in text for kw in keywords):
                            print(f"[Command] {cmd}")
                            self._publish_intent(cmd, text)
                            self.listening_for_command = False
                    return

                # 2. Not activated but command spoken
                if not self.listening_for_command:
                    for cmd, keywords in self.commands.items():
                        if any(kw in text for kw in keywords):
                            print("[Wake] Please say wake word first")
                            break
                    return

                # 3. Activated: check emergency and commands
                if any(ew in text for ew in self.emergency_words):
                    print("[Emergency] !!!")
                    self._publish_intent("emergency", text)

                for cmd, keywords in self.commands.items():
                    if any(kw in text for kw in keywords):
                        print(f"[Command] {cmd}")
                        self._publish_intent(cmd, text)

        else:
            partial = json.loads(self.rec.PartialResult())
            if partial.get('partial'):
                print(f"\r[Partial] {partial['partial']:30}", end='')

    def _publish_intent(self, intent, text):
        msg = {"intent": intent, "text": text, "timestamp": time.time()}
        # === Only change is here ===
        if self.mqtt:
            self.mqtt.publish("voice/intent", json.dumps(msg))
        else:
            # Print the message instead (for local testing)
            print(f"[MQTT-DEBUG] voice/intent: {json.dumps(msg)}")
