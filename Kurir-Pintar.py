import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import random
import math
import time
import heapq

class SelfDrivingCarSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Self-Driving Car Simulator with AI")
        
        # Colors
        self.road_color = (90, 90, 90)
        self.border_color = (255, 255, 255)
        self.target_color = (0, 255, 0)
        
        # Car state
        self.car_pos = [100, 100]
        self.target_pos = [300, 300]
        self.is_moving = False
        self.speed = 3
        self.car_angle = 0
        self.collisions = 0
        self.track_pixels = []
        
        # AI enhancements
        self.visited_positions = []
        self.avoidance_mode = False
        self.path = []
        
        # Setup UI
        self.create_widgets()
        self.load_default_map()

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Button(frame, text="Load Default Map", command=self.load_default_map).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Load Custom Map", command=self.load_custom_map).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Start", command=self.start).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Stop", command=self.stop).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Randomize", command=self.randomize_positions).pack(side=tk.LEFT, padx=5)
        
        self.pathfinding_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Use Pathfinding", variable=self.pathfinding_var).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()

        self.collision_label = tk.Label(self.root, text="Border Crossings: 0")
        self.collision_label.pack()

    def load_default_map(self):
        img = Image.new("RGB", (800, 600), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 700, 500], fill=self.road_color, outline=self.border_color, width=10)
        self.process_map(img)

    def load_custom_map(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
        if path:
            try:
                img = Image.open(path)
                self.process_map(img)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def process_map(self, img):
        self.track_image = img.convert("RGB")
        self.tk_image = ImageTk.PhotoImage(self.track_image)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        
        width, height = img.size
        self.track_pixels = []
        
        for x in range(width):
            for y in range(height):
                if self.track_image.getpixel((x, y)) == self.road_color:
                    self.track_pixels.append((x, y))
        
        self.reset()

    def is_on_road(self, pos):
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self.track_image.width and 0 <= y < self.track_image.height:
            return self.track_image.getpixel((x, y)) == self.road_color
        return False

    def calculate_path(self):
        """A* pathfinding algorithm"""
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        start = (int(self.car_pos[0]), int(self.car_pos[1]))
        goal = (int(self.target_pos[0]), int(self.target_pos[1]))
        
        neighbors = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        close_set = set()
        came_from = {}
        gscore = {start:0}
        fscore = {start:heuristic(start, goal)}
        oheap = []
        
        heapq.heappush(oheap, (fscore[start], start))
        
        while oheap:
            current = heapq.heappop(oheap)[1]
            
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]
                
            close_set.add(current)
            for i, j in neighbors:
                neighbor = current[0] + i, current[1] + j
                if 0 <= neighbor[0] < self.track_image.width and 0 <= neighbor[1] < self.track_image.height:
                    if self.track_image.getpixel(neighbor) != self.road_color:
                        continue
                        
                    tentative_g_score = gscore[current] + heuristic(current, neighbor)
                    
                    if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, float('inf')):
                        continue
                        
                    if tentative_g_score < gscore.get(neighbor, float('inf')) or neighbor not in [i[1] for i in oheap]:
                        came_from[neighbor] = current
                        gscore[neighbor] = tentative_g_score
                        fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                        heapq.heappush(oheap, (fscore[neighbor], neighbor))
        
        return []  # No path found

    def sense_environment(self):
        """Enhanced 8-direction sensor"""
        sensor_range = 30
        angles = [0, -math.pi/4, math.pi/4, -math.pi/2, math.pi/2, 
                 -math.pi/8, math.pi/8, -3*math.pi/4, 3*math.pi/4]
        readings = []

        for angle_offset in angles:
            angle = self.car_angle + angle_offset
            x = int(self.car_pos[0] + math.cos(angle) * sensor_range)
            y = int(self.car_pos[1] + math.sin(angle) * sensor_range)
            
            if 0 <= x < self.track_image.width and 0 <= y < self.track_image.height:
                pixel = self.track_image.getpixel((x, y))
                if pixel == self.border_color:
                    readings.append(1)  # Border detected
                elif pixel == self.road_color:
                    readings.append(0)  # Road
                else:
                    readings.append(2)  # Off-road
            else:
                readings.append(2)  # Out of bounds
                
        return readings

    def decide_direction(self, readings):
        """Advanced decision making with pathfinding"""
        if self.pathfinding_var.get() and not self.path:
            self.path = self.calculate_path()
        
        # If using pathfinding and we have a path
        if self.pathfinding_var.get() and self.path:
            next_pos = self.path[0]
            dx = next_pos[0] - self.car_pos[0]
            dy = next_pos[1] - self.car_pos[1]
            target_angle = math.atan2(dy, dx)
            
            # Remove reached points from path
            if math.hypot(dx, dy) < 10:
                self.path.pop(0)
                
            angle_diff = (target_angle - self.car_angle + math.pi) % (2*math.pi) - math.pi
            max_steering = math.pi/6  # 30 degrees max turn
            return self.car_angle + max(-max_steering, min(max_steering, angle_diff))
        
        # Obstacle avoidance logic
        front_readings = readings[:5]
        if any(r == 1 for r in front_readings[:3]):  # Obstacle ahead
            self.avoidance_mode = True
            
        if self.avoidance_mode:
            if all(r == 0 for r in front_readings[:3]):
                self.avoidance_mode = False
            else:
                # Prefer turning left (standard traffic rules)
                if readings[3] == 0:  # Left clear
                    return self.car_angle - math.pi/8
                elif readings[4] == 0:  # Right clear
                    return self.car_angle + math.pi/8
                else:
                    return self.car_angle + math.pi  # Turn around
        
        # Default: head toward target
        dx = self.target_pos[0] - self.car_pos[0]
        dy = self.target_pos[1] - self.car_pos[1]
        target_angle = math.atan2(dy, dx)
        
        angle_diff = (target_angle - self.car_angle + math.pi) % (2*math.pi) - math.pi
        max_steering = math.pi/8  # 22.5 degrees max turn
        return self.car_angle + max(-max_steering, min(max_steering, angle_diff))

    def move_car(self):
        if not self.is_moving:
            return
            
        readings = self.sense_environment()
        self.car_angle = self.decide_direction(readings)
        
        # Adaptive speed
        front_clear = all(r == 0 for r in readings[:3])
        self.speed = 5 if front_clear else 2
        
        direction = (math.cos(self.car_angle), math.sin(self.car_angle))
        self.car_pos[0] += direction[0] * self.speed
        self.car_pos[1] += direction[1] * self.speed
        
        # Track border crossings
        if not self.is_on_road(self.car_pos):
            self.collisions += 1
            self.collision_label.config(text=f"Border Crossings: {self.collisions}")
        
        self.draw()
        
        # Check if reached target
        if math.hypot(self.target_pos[0]-self.car_pos[0], self.target_pos[1]-self.car_pos[1]) < 20:
            self.is_moving = False
            messagebox.showinfo("Arrived", "Target reached successfully!")
            return
            
        self.root.after(30, self.move_car)

    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        
        # Draw path if available
        if self.pathfinding_var.get() and self.path:
            for i in range(len(self.path)-1):
                self.canvas.create_line(self.path[i][0], self.path[i][1], 
                                      self.path[i+1][0], self.path[i+1][1],
                                      fill="blue", width=2)
        
        # Draw car (triangle)
        car_size = 15
        points = [
            (self.car_pos[0] + math.cos(self.car_angle) * car_size,
             self.car_pos[1] + math.sin(self.car_angle) * car_size),
            (self.car_pos[0] + math.cos(self.car_angle + 2*math.pi/3) * car_size,
             self.car_pos[1] + math.sin(self.car_angle + 2*math.pi/3) * car_size),
            (self.car_pos[0] + math.cos(self.car_angle - 2*math.pi/3) * car_size,
             self.car_pos[1] + math.sin(self.car_angle - 2*math.pi/3) * car_size)
        ]
        self.canvas.create_polygon(points, fill="blue", outline="black")
        
        # Draw target (larger circle)
        target_size = 20
        self.canvas.create_oval(
            self.target_pos[0]-target_size, self.target_pos[1]-target_size,
            self.target_pos[0]+target_size, self.target_pos[1]+target_size,
            fill="green", outline="black"
        )

    def start(self):
        if not self.is_moving:
            self.is_moving = True
            self.path = self.calculate_path() if self.pathfinding_var.get() else []
            self.move_car()

    def stop(self):
        self.is_moving = False

    def reset(self):
        self.stop()
        self.car_pos = [100, 100]
        self.target_pos = [300, 300]
        self.car_angle = 0
        self.collisions = 0
        self.path = []
        self.collision_label.config(text="Border Crossings: 0")
        self.draw()

    def randomize_positions(self):
        if self.track_pixels:
            self.car_pos = list(random.choice(self.track_pixels))
            valid = [p for p in self.track_pixels if math.dist(p, self.car_pos) > 100]
            if valid:
                self.target_pos = list(random.choice(valid))
            self.path = self.calculate_path() if self.pathfinding_var.get() else []
            self.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = SelfDrivingCarSimulator(root)
    root.mainloop()