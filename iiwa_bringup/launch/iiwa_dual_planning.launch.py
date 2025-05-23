# Copyright 2022 ICube Laboratory, University of Strasbourg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_param_builder import ParameterBuilder, load_yaml, load_xacro
import os
from ament_index_python.packages import get_package_share_directory
from launch_param_builder import ParameterBuilder

def _octomap_launch_params(params: ParameterBuilder):
    params.yaml("moveit2/sensors_virtual_pointcloud.yaml")
    params.parameter("octomap_frame", "world")
    params.parameter("octomap_resolution", 0.02)
    params.parameter("max_range", 5.0)
    return params.to_dict()
    
def generate_launch_description():
    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            'description_package',
            default_value='iiwa_description',
            description='Description package with robot URDF/xacro files. Usually the argument \
                         is not set, it enables use of a custom description.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'description_file',
            default_value='iiwa.config.xacro',
            description='URDF/XACRO description file with the robot.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'prefix',
            default_value='""',
            description='Prefix of the joint names, useful for multi-robot setup. \
                         If changed than also joint names in the controllers \
                         configuration have to be updated. Expected format "<prefix>/"',
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            'srdf',
            default_value='iiwa.srdf.xarco',
            description='SRDF file name"',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'namespace',
            default_value='/',
            description='Namespace of launched nodes, useful for multi-robot setup. \
                         If changed than also the namespace in the controllers \
                         configuration needs to be updated. Expected format "<ns>/".',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'start_rviz',
            default_value='true',
            description='Start RViz2 automatically with this launch file.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'base_frame_file',
            default_value='base_frame.yaml',
            description='Configuration file of robot base frame wrt World.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'use_sim',
            default_value='false',
            description='Start robot in Gazebo simulation.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'show_aruco_board',
            default_value='false',
            description='Show ARUCO board.',
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            'add_gripper_links',
            default_value='true',
            description='Add end-effector for each robot',
        )
    )

    # Initialize Arguments
    description_package = LaunchConfiguration('description_package')
    description_file = LaunchConfiguration('description_file')
    srdf = LaunchConfiguration('srdf')
    prefix = LaunchConfiguration('prefix')
    start_rviz = LaunchConfiguration('start_rviz')
    base_frame_file = LaunchConfiguration('base_frame_file')
    namespace = LaunchConfiguration('namespace')
    use_sim = LaunchConfiguration('use_sim')
    show_aruco_board = LaunchConfiguration('show_aruco_board')
    add_gripper_links = LaunchConfiguration('add_gripper_links')


    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [FindPackageShare(description_package), 'config', description_file]
            ),
            ' ',
            'prefix:=',
            prefix,
            ' ',
            'base_frame_file:=',
            base_frame_file,
            ' ',
            'description_package:=',
            description_package,
            ' ',
            'show_aruco_board:=',
            show_aruco_board,
            ' ',
            'add_gripper_links:=',
            add_gripper_links,
            ' ',
            'namespace:=',
            namespace,
        ]
    )

    robot_description = {'robot_description': robot_description_content}

    # Get SRDF via xacro
    robot_description_semantic_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare(description_package), "srdf", "iiwa_dual.srdf.xacro"]
            ),
            " ",
            "name:=",
            "iiwa",
            " ",
            "prefix:=",
            prefix,
            " ",
            'show_aruco_board:=',
            show_aruco_board,
            ' ',
            'description_package:=',
            description_package,
           
        ]
    )

    robot_description_semantic = {
        'robot_description_semantic': robot_description_semantic_content
    }

    # Get planning parameters
    robot_description_planning_joint_limits = PathJoinSubstitution([
            FindPackageShare(description_package), "moveit2", "iiwa_dual_joint_limits.yaml",
        ]
    )

    robot_description_planning_cartesian_limits = PathJoinSubstitution([
            FindPackageShare(description_package), "moveit2", "iiwa_cartesian_limits.yaml",
        ]
    )

    move_group_capabilities = {
        "capabilities": """pilz_industrial_motion_planner/MoveGroupSequenceAction \
            pilz_industrial_motion_planner/MoveGroupSequenceService"""
    }

    robot_description_kinematics = PathJoinSubstitution(
        [FindPackageShare(description_package), "moveit2", "dual_kinematics.yaml"]
    )

    planning_pipelines_config = PathJoinSubstitution([
            FindPackageShare(description_package), "moveit2", "dual_planning_pipelines_config.yaml",
        ]
    )

    ompl_planning_config = PathJoinSubstitution([
            FindPackageShare(description_package), "moveit2", "dual_ompl_planning.yaml",
        ]
    )

    moveit_controllers = PathJoinSubstitution(
        [FindPackageShare(description_package),
            "moveit2", "iiwa_dual_moveit_controller_config.yaml"]
    )

    trajectory_execution = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }

    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_monitored_planning_scene": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
        "publish_robot_description":True, 
 	    "publish_robot_description_semantic":True
    }

   
    params_movegroup = ParameterBuilder('iiwa_description')
   
   
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        namespace=namespace,
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning_cartesian_limits,
            robot_description_planning_joint_limits,
            planning_pipelines_config,
            ompl_planning_config,
            trajectory_execution,
            moveit_controllers,
            planning_scene_monitor_parameters,
       #     move_group_capabilities,
       #     {"use_sim_time": True}
          ] 
        + [_octomap_launch_params(params_movegroup)],
       # arguments=['--ros-args', '--log-level', 'debug', "--log-level",  "rcl:=INFO"]
    )

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare(description_package), 'rviz', 'iiwa.rviz']
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config_file],
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_planning_cartesian_limits,
            robot_description_planning_joint_limits,
            robot_description_kinematics,
            planning_pipelines_config,
            ompl_planning_config,
      #      {"use_sim_time": True}
        ],
        condition=IfCondition(start_rviz),
    )

    nodes = [
        move_group_node,
        rviz_node,
    ]

    return LaunchDescription(declared_arguments + nodes)
