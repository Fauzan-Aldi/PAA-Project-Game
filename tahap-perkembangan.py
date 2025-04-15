import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import random
import math

class SelfDrivingCarSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Self-Driving Car Simulator")
        
        # Warna
        self.road_color = (90, 90, 90)
        self.wall_color = (243, 114, 4)  # Pagar warna #f37204
        self.target_color = (0, 255, 0)
        
        # State
        self.car_pos = [100, 100]
        self.target_pos = [300, 300]
        self.is_moving = False
        self.speed = 3
        self.car_angle = 0
        self.collisions = 0
        self.track_pixels = []

        # Setup UI
        self.create_widgets()
        self.load_default_map()

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Button(frame, text="Load Map", command=self.load_map).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Start", command=self.start).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Stop", command=self.stop).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Acak", command=self.randomize_positions).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()

        self.collision_label = tk.Label(self.root, text="Tabrakan: 0")
        self.collision_label.pack()

    def load_default_map(self):
        img = Image.new("RGB", (800, 600), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 700, 500], fill=self.road_color, outline=self.wall_color, width=10)
        self.process_map(img)

    def load_map(self):
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
        self.track_pixels = [
            (x, y) for x in range(img.width) for y in range(img.height)
            if self.track_image.getpixel((x, y)) == self.road_color
        ]
        self.reset()

    def is_valid_position(self, pos):
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self.track_image.width and 0 <= y < self.track_image.height:
            px = self.track_image.getpixel((x, y))
            return px == self.road_color or px == self.target_color
        return False

    def sense_environment(self):
        """Sensor 5 arah: depan, kiri, kanan, diagonal kiri-kanan"""
        sensor_range = 20
        angles = [0, -math.pi/4, math.pi/4, -math.pi/2, math.pi/2]  # depan, kiri, kanan, atas, bawah
        readings = []

        for angle_offset in angles:
            angle = self.car_angle + angle_offset
            x = int(self.car_pos[0] + math.cos(angle) * sensor_range)
            y = int(self.car_pos[1] + math.sin(angle) * sensor_range)
            if 0 <= x < self.track_image.width and 0 <= y < self.track_image.height:
                pixel = self.track_image.getpixel((x, y))
                if pixel == self.wall_color:
                    readings.append(1)  # Deteksi pagar
                elif pixel == self.road_color:
                    readings.append(0)  # Aman
                else:
                    readings.append(2)  # Keluar jalan
            else:
                readings.append(2)  # Di luar gambar
        return readings

    def decide_direction(self, readings):
        """Keputusan berdasarkan sensor sederhana"""
        front, left_diag, right_diag, left, right = readings

        if front == 0:
            return self.car_angle  # Lurus
        elif left_diag == 0:
            return self.car_angle - math.pi / 6  # Belok kiri
        elif right_diag == 0:
            return self.car_angle + math.pi / 6  # Belok kanan
        elif left == 0:
            return self.car_angle - math.pi / 4
        elif right == 0:
            return self.car_angle + math.pi / 4
        else:
            return self.car_angle + math.pi  # Putar arah (mentok semua sisi)

    def move_car(self):
        if not self.is_moving:
            return

        readings = self.sense_environment()
        new_angle = self.decide_direction(readings)
        self.car_angle = new_angle

        direction = (math.cos(self.car_angle), math.sin(self.car_angle))
        new_pos = [
            self.car_pos[0] + direction[0] * self.speed,
            self.car_pos[1] + direction[1] * self.speed
        ]

        if self.is_valid_position(new_pos):
            self.car_pos = new_pos
        else:
            self.collisions += 1
            self.collision_label.config(text=f"Tabrakan: {self.collisions}")
            self.reset()
            return

        self.draw()

        # Cek jarak ke target
        dx = self.target_pos[0] - self.car_pos[0]
        dy = self.target_pos[1] - self.car_pos[1]
        if math.hypot(dx, dy) < 10:
            self.is_moving = False
            messagebox.showinfo("Info", "Target tercapai!")
            return

        self.root.after(30, self.move_car)

    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

        car_size = 15
        angle = self.car_angle
        points = [
            (self.car_pos[0] + math.cos(angle) * car_size,
             self.car_pos[1] + math.sin(angle) * car_size),
            (self.car_pos[0] + math.cos(angle + 2*math.pi/3) * car_size,
             self.car_pos[1] + math.sin(angle + 2*math.pi/3) * car_size),
            (self.car_pos[0] + math.cos(angle - 2*math.pi/3) * car_size,
             self.car_pos[1] + math.sin(angle - 2*math.pi/3) * car_size)
        ]
        self.canvas.create_polygon(points, fill="blue", outline="black")

        self.canvas.create_rectangle(
            self.target_pos[0]-8, self.target_pos[1]-8,
            self.target_pos[0]+8, self.target_pos[1]+8,
            fill="green"
        )

    def start(self):
        if not self.is_moving:
            self.is_moving = True
            self.move_car()

    def stop(self):
        self.is_moving = False

    def reset(self):
        self.stop()
        self.car_pos = [100, 100]
        self.target_pos = [300, 300]
        self.car_angle = 0
        self.draw()

    def randomize_positions(self):
        if self.track_pixels:
            self.car_pos = list(random.choice(self.track_pixels))
            valid = [p for p in self.track_pixels if math.dist(p, self.car_pos) > 100]
            if valid:
                self.target_pos = list(random.choice(valid))
            dx = self.target_pos[0] - self.car_pos[0]
            dy = self.target_pos[1] - self.car_pos[1]
            self.car_angle = math.atan2(dy, dx)
            self.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = SelfDrivingCarSimulator(root)
    root.mainloop()
