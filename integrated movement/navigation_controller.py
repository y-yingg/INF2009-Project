#!/usr/bin/env python3
# navigation_controller.py

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Point, Quaternion
from std_msgs.msg import Header
import math
import sys
import json
import time

class NavigationController(Node):
    def __init__(self):
        super().__init__('navigation_controller')
        
        # Create action client for navigation
        self.action_client = ActionClient(
            self, 
            NavigateToPose, 
            'navigate_to_pose'
        )
        
        self.get_logger().info('Navigation Controller initialized')
        
        # Dictionary to store named locations
        self.locations = {}
        
    def send_goal(self, x, y, theta=0.0, frame_id='map', wait=True):
        """
        Send a navigation goal to specific coordinates
        
        Args:
            x, y: Coordinates in meters
            theta: Orientation in radians (0 = forward)
            frame_id: Coordinate frame (usually 'map')
            wait: Whether to wait for result
        """
        
        # Convert theta to quaternion
        q = self.euler_to_quaternion(0, 0, theta)
        
        # Create goal message
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped(
            header=Header(
                stamp=self.get_clock().now().to_msg(),
                frame_id=frame_id
            ),
            pose=Point(x=x, y=y, z=0.0),
            orientation=Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
        )
        
        self.get_logger().info(f'Sending goal: x={x:.2f}, y={y:.2f}, theta={theta:.2f}')
        
        # Wait for action server
        if not self.action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Action server not available')
            return False
        
        # Send goal
        send_goal_future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        
        if wait:
            rclpy.spin_until_future_complete(self, send_goal_future)
            goal_handle = send_goal_future.result()
            
            if not goal_handle.accepted:
                self.get_logger().error('Goal rejected')
                return False
            
            self.get_logger().info('Goal accepted')
            
            # Wait for result
            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)
            
            result = result_future.result()
            if result.status == 4:  # SUCCEEDED
                self.get_logger().info('Goal reached successfully!')
                return True
            else:
                self.get_logger().error(f'Failed with status: {result.status}')
                return False
        
        return True
    
    def feedback_callback(self, feedback_msg):
        """Optional: Monitor navigation progress"""
        feedback = feedback_msg.feedback
        distance = feedback.distance_remaining
        self.get_logger().debug(f'Distance to goal: {distance:.2f}m')
    
    def euler_to_quaternion(self, roll, pitch, yaw):
        """Convert Euler angles to quaternion"""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        q = [0] * 4
        q[0] = sr * cp * cy - cr * sp * sy  # x
        q[1] = cr * sp * cy + sr * cp * sy  # y
        q[2] = cr * cp * sy - sr * sp * cy  # z
        q[3] = cr * cp * cy + sr * sp * sy  # w
        
        return q
    
    def save_current_location(self, name):
        """Save robot's current position as a named location"""
        # Get current pose from /amcl_pose
        from nav2_msgs.msg import ParticleCloud
        
        msg = self.get_clock().now().to_msg()
        
        # Simple approach: get from transform
        from tf2_ros import TransformListener, Buffer
        tf_buffer = Buffer()
        tf_listener = TransformListener(tf_buffer, self)
        
        try:
            trans = tf_buffer.lookup_transform(
                'map', 
                'base_link', 
                rclpy.time.Time()
            )
            
            self.locations[name] = {
                'x': trans.transform.translation.x,
                'y': trans.transform.translation.y,
                'theta': self.quaternion_to_euler(
                    trans.transform.rotation.x,
                    trans.transform.rotation.y,
                    trans.transform.rotation.z,
                    trans.transform.rotation.w
                )[2]  # Get yaw
            }
            
            self.get_logger().info(f'Saved location "{name}": {self.locations[name]}')
            return True
            
        except Exception as e:
            self.get_logger().error(f'Failed to get current pose: {e}')
            return False
    
    def quaternion_to_euler(self, x, y, z, w):
        """Convert quaternion to Euler angles"""
        import math
        
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(t0, t1)
        
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch = math.asin(t2)
        
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(t3, t4)
        
        return roll, pitch, yaw
    
    def load_locations(self, filename='locations.json'):
        """Load named locations from file"""
        try:
            with open(filename, 'r') as f:
                self.locations = json.load(f)
            self.get_logger().info(f'Loaded {len(self.locations)} locations')
        except FileNotFoundError:
            self.get_logger().info('No locations file found')
    
    def save_locations(self, filename='locations.json'):
        """Save named locations to file"""
        with open(filename, 'w') as f:
            json.dump(self.locations, f, indent=2)
        self.get_logger().info(f'Saved {len(self.locations)} locations')
    
    def go_to_location(self, name, wait=True):
        """Go to a named location"""
        if name not in self.locations:
            self.get_logger().error(f'Location "{name}" not found')
            return False
        
        loc = self.locations[name]
        return self.send_goal(loc['x'], loc['y'], loc['theta'], wait=wait)
    
    def multi_point_navigation(self, points, wait_between=True):
        """
        Navigate through multiple points
        
        points: List of tuples (x, y, theta) or location names
        """
        for i, point in enumerate(points):
            self.get_logger().info(f'Navigating to point {i+1}/{len(points)}')
            
            if isinstance(point, str):
                # Point is a location name
                success = self.go_to_location(point, wait=True)
            else:
                # Point is coordinates
                x, y, theta = point
                success = self.send_goal(x, y, theta, wait=True)
            
            if not success:
                self.get_logger().error(f'Failed to reach point {i+1}')
                return False
            
            # Brief pause between goals
            if wait_between and i < len(points) - 1:
                time.sleep(2)
        
        self.get_logger().info('Multi-point navigation complete')
        return True


def main(args=None):
    rclpy.init(args=args)
    controller = NavigationController()
    
    # Example usage:
    
    # 1. Send a goal to specific coordinates
    # controller.send_goal(x=2.5, y=1.8, theta=0.0)
    
    # 2. Save current position as named location
    # controller.save_current_location('kitchen')
    # controller.save_current_location('living_room')
    # controller.save_locations()
    
    # 3. Load saved locations and go to one
    # controller.load_locations()
    # controller.go_to_location('kitchen')
    
    # 4. Multi-point navigation
    # points = [
    #     ('kitchen'),
    #     ('living_room'),
    #     (3.5, 2.0, 1.57)  # x, y, theta
    # ]
    # controller.multi_point_navigation(points)
    
    # 5. Command line interface
    if len(sys.argv) > 1:
        if sys.argv[1] == '--save' and len(sys.argv) == 3:
            controller.save_current_location(sys.argv[2])
            controller.save_locations()
        elif sys.argv[1] == '--list':
            controller.load_locations()
            for name, loc in controller.locations.items():
                print(f"{name}: x={loc['x']:.2f}, y={loc['y']:.2f}, theta={loc['theta']:.2f}")
        elif len(sys.argv) == 2:
            controller.load_locations()
            controller.go_to_location(sys.argv[1])
        elif len(sys.argv) == 3:
            x = float(sys.argv[1])
            y = float(sys.argv[2])
            controller.send_goal(x, y)
        elif len(sys.argv) == 4:
            x = float(sys.argv[1])
            y = float(sys.argv[2])
            theta = float(sys.argv[3])
            controller.send_goal(x, y, theta)
    else:
        # Demo: Save current location and go back to it
        controller.save_current_location('start')
        controller.send_goal(x=1.0, y=1.0, theta=0.0)
        time.sleep(2)
        controller.go_to_location('start')
    
    rclpy.shutdown()


if __name__ == '__main__':
    main()
