import cv2
import numpy as np
import math
from queue import Queue, deque
import time
import matplotlib.pyplot as plt
from simplepriorityqueue import SimplePriorityQueue
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class PathExplorer:
    
    # action_angle: minimum turn angle (in degrees) that the bot can make between two positions
    def find_path(self, initial_pos, target_pos, orientation, step_size, cspace_map, heuristic_func, action_angle=30):
        initial_pos = (initial_pos[0], initial_pos[1])
        target_pos = (target_pos[0], target_pos[1])
        
        if (not self.is_position_valid(initial_pos, cspace_map)) or (not self.is_position_valid(target_pos, cspace_map)):
            print("Either initial or target position lies in the obstacle space or out of the configuration space. Please check and try again.")
            return

        node_queue = SimplePriorityQueue()
        visited_nodes_set = set()
        visited_nodes_list = []
    
        initial_node = {
            'pos': initial_pos,
            'orientation': orientation,
            'path': [],
            'parent': initial_pos,
            'cost': 0, 
            'cost_to_go': heuristic_func(initial_pos, target_pos)
            }

        cost_update_map = {}
        cost_update_map[self.get_rounded_pos_orient(initial_node)] = 0

        is_target_found = False

        # cost to reach to the node as a key to sort
        node_queue.put(0, initial_node)

        msg_queue = Queue()
        self.init_msg_queue(msg_queue)
        count = 0
        start = time.clock()
        while (not node_queue.isempty()) and not is_target_found:
            count +=  1
            #print('count: ', count)
            if (not msg_queue.empty()) and (count % 5000 == 0):
                print(msg_queue.get())
            
            current_node = node_queue.get()[1]
            node_pos_orient = self.get_rounded_pos_orient(current_node)
            if node_pos_orient not in visited_nodes_set:
                visited_nodes_list.append(current_node)
            visited_nodes_set.add(node_pos_orient)

            if self.is_within_goal_region(current_node['pos'], target_pos):
                print('\nTarget found')
                is_target_found = True
                solution_path, path_cost = current_node['path'], current_node['cost'] 
            else:
                next_positions = self.get_next_positions(current_node, cspace_map, target_pos, step_size, action_angle, heuristic_func)
                for node in next_positions:
                    rounded_child = self.get_rounded_pos_orient(node)
                    if rounded_child not in visited_nodes_set:
                        old_cost_for_node = math.inf if rounded_child not in cost_update_map.keys() else cost_update_map[rounded_child]
                        new_cost_for_node = node['cost'] + node['cost_to_go']
                        if old_cost_for_node > new_cost_for_node:
                            cost_update_map[rounded_child] = node['cost']
                            node_queue.put(new_cost_for_node, node)

        end = time.clock()

        print('Time taken:', end-start, 'seconds(approx:', int((end-start)/60),'min:', int((end-start)%60), 'sec)' )
        if is_target_found:
            print('Cost of the path: ', path_cost, 'units')
            self.start_visualization(initial_node, target_pos, visited_nodes_list, solution_path, action_angle, step_size, cspace_map)
        else:
            print('Target cannot be reached')

        
    def is_within_goal_region(self, position, target_pos, goal_threshold_radius=1.5):
        return math.sqrt((target_pos[0]-position[0])**2 + (target_pos[1]-position[1])**2) <= goal_threshold_radius

    def get_rounded_pos_orient(self, node, pos_threshold=0.5, orientation_threshold=30):
        node_pos_y, node_pos_x = node['pos']
        orientation = node['orientation']
        node_pos_x = self.roundoff_value(node_pos_x, pos_threshold)
        node_pos_y = self.roundoff_value(node_pos_y, pos_threshold)
        orientation = self.roundoff_value(orientation, orientation_threshold)

        return (node_pos_x, node_pos_y, orientation)

    def roundoff_value(self, value, roundoff_threshold):
        return (round(value/roundoff_threshold))*roundoff_threshold

    def get_next_positions(self, node, cspace_map, target_pos, step_size, action_angle, heuristic_func):
        
        action_angle_map = {
            'TWOTHETA_U': 2*action_angle,
            'THETA_U': action_angle,
            'THETA_Z': 0,
            'THETA_D': -action_angle,
            'TWOTHETA_D': -2*action_angle
            }
              
        next_postions = []
        
        node_pos = list(node['pos'])
        for action in action_angle_map:
            #print(action) # TODO: to be removed
            next_orient = self.get_new_orientation(node['orientation'], action_angle_map[action])
            next_pos = self.get_new_position(node_pos, next_orient, step_size)
            if self.is_position_valid(next_pos, cspace_map):
                node_path = node['path'].copy()
                node_path.append(action)
                
                next_postions.append({
                    'pos': tuple(next_pos),
                    'orientation': next_orient,
                    'path': node_path,
                    'parent': node['pos'],
                    'cost': node['cost'] + step_size,
                    'cost_to_go': heuristic_func(next_pos, target_pos)
                })
        return next_postions
    
    def get_new_orientation(self, old_orienation, delta_angle):
        new_orientation = old_orienation + delta_angle
        if new_orientation < 0:
            new_orientation = 360 + new_orientation
        elif new_orientation >= 360:
            new_orientation = new_orientation % 360
        return new_orientation
    
    def get_new_position(self, node_pos, new_orient, step_size):
        new_orient_rad = new_orient * math.pi/180
        action = [step_size*math.sin(new_orient_rad), step_size*math.cos(new_orient_rad)]
        return np.add(node_pos, action)
                
        
    def is_position_valid(self, position, cspace_map):
        #BLUE = (255, 0, 0)
        point_not_in_obstacle_area = False
        if (0 <= position[0] <= cspace_map.shape[0] and 0 <= position[1] <= cspace_map.shape[1]):
            #point_not_in_obstacle_area = not (tuple(cspace_map[position[0], position[1]]) == BLUE)
            point_not_in_obstacle_area = True
        
        return point_not_in_obstacle_area

    
    def start_visualization(self, initial_node, target_pos, visited_nodes, path, action_angle, step_size, cspace_map):

        action_angle_map = {
            'TWOTHETA_U': 2*action_angle,
            'THETA_U': action_angle,
            'THETA_Z': 0,
            'THETA_D': -action_angle,
            'TWOTHETA_D': -2*action_angle
            }


        fig, ax = plt.subplots()
        plt.xlim(0,cspace_map.shape[1])
        plt.ylim(0,cspace_map.shape[0])
        plt.grid()

        ax.set_aspect('equal')

        a_circle = plt.Circle((target_pos[1], target_pos[0]), 1.5)
        ax.add_artist(a_circle)
        
        dots = {0: '    ', 1: '.   ', 2: '..  ', 3: '... ', 4: '....'} 
        num_dots = len(dots)
        print('Visualization in process...\n')
        def animate(i):
            if i < len(visited_nodes):
                ax.set_title('Exploring Configuration Space' + str(dots[i%num_dots]), fontsize=13)
                parent_y, parent_x = visited_nodes[i]['parent']
                node_y, node_x = visited_nodes[i]['pos']
                ax.quiver(parent_x, parent_y, node_x-parent_x, node_y-parent_y, units='xy' ,scale=1, color='orange')
                
            else:
                goal_reached_str = 'Goal Reached. Cost: ' + str(len(path)*step_size) + 'units' 
                ax.set_title(goal_reached_str, fontsize=13)
                
                prev_pos, prev_orient = list(initial_node['pos']), initial_node['orientation']
                for action in path:
                    next_orient = self.get_new_orientation(prev_orient, action_angle_map[action])
                    next_pos = self.get_new_position(prev_pos, next_orient, step_size)

                    parent_y, parent_x = prev_pos[0], prev_pos[1]
                    node_y, node_x = next_pos[0], next_pos[1]
                    ax.quiver(parent_x, parent_y, node_x-parent_x, node_y-parent_y, units='xy' ,scale=1, color='b')
                    prev_pos = next_pos
                    prev_orient = next_orient
                
        
        anim = FuncAnimation(fig, animate, frames=len(visited_nodes)+1, interval=10, blit=False, repeat=False)

        fig.show()
        plt.draw()
        plt.show()

        anim.save('a_star_exploration.gif', writer='imagemagick', fps=30)

        print('\nVisualization Complete.')

    
    def init_msg_queue(self, msg_queue):
        with open('msgs.txt', 'r') as msg_file:
            msg_queue.queue = deque(msg_file.readlines())


