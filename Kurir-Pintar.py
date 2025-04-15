import tkinter as tk # Mengimpor modul tkinter sebagai tk untuk membuat antarmuka grafis pengguna (GUI)
from tkinter import filedialog, messagebox # Mengimpor dialog file dan kotak pesan dari modul tkinter
# Mengimpor PIL (Python Imaging Library) untuk manipulasi gambar
# Image: untuk memuat gambar
# ImageTk: untuk mengonversi gambar ke format yang bisa digunakan oleh tkinter
# ImageDraw: untuk menggambar di atas gambar
from PIL import Image, ImageTk, ImageDraw
import random # Mengimpor modul random untuk menghasilkan angka acak
import math # Mengimpor modul math untuk operasi matematika seperti sqrt, sin, cos, dll
import time # Mengimpor modul time untuk pengukuran waktu (delay, timer, dll)
import heapq # Mengimpor heapq, modul untuk struktur data heap 

# Kelas utama untuk mensimulasikan mobil self-driving menggunakan AI
class SelfDrivingCarSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Self-Driving Car Simulator with AI")  # Judul jendela aplikasi
        
        # Warna-warna dasar untuk jalan, batas, dan target
        self.road_color = (90, 90, 90)
        self.border_color = (255, 255, 255)
        self.target_color = (0, 255, 0)
        
        # Status awal mobil
        self.car_pos = [100, 100]  # Posisi awal mobil
        self.target_pos = [300, 300]  # Posisi target
        self.is_moving = False  # Status gerak mobil
        self.speed = 3  # Kecepatan awal
        self.car_angle = 0  # Sudut arah mobil
        self.collisions = 0  # Jumlah tabrakan/border crossings
        self.track_pixels = []  # Piksel yang dianggap jalan
        
        # Variabel untuk AI dan pathfinding
        self.visited_positions = []  # Posisi yang sudah dikunjungi
        self.avoidance_mode = False  # Mode menghindar aktif atau tidak
        self.path = []  # Jalur yang dihitung oleh pathfinding
        
        # Inisialisasi tampilan antarmuka pengguna
        self.create_widgets()
        self.load_default_map()

    # Membuat tombol-tombol dan kanvas di GUI
    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        # Tombol-tombol kontrol
        tk.Button(frame, text="Load Default Map", command=self.load_default_map).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Load Custom Map", command=self.load_custom_map).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Start", command=self.start).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Stop", command=self.stop).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Randomize", command=self.randomize_positions).pack(side=tk.LEFT, padx=5)
        
        # Checkbox untuk mengaktifkan pathfinding
        self.pathfinding_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Use Pathfinding", variable=self.pathfinding_var).pack(side=tk.LEFT, padx=5)

        # Kanvas tempat peta dan mobil akan digambar
        self.canvas = tk.Canvas(self.root, width=1000, height=700)
        self.canvas.pack()

        # Label jumlah tabrakan
        self.collision_label = tk.Label(self.root, text="Border Crossings: 0")
        self.collision_label.pack()

    # Menampilkan layar loading saat memproses gambar
    def show_loading_screen(self):
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Loading")
        self.loading_window.geometry("300x100")
        self.loading_window.transient(self.root)
        
        tk.Label(self.loading_window, text="Processing image, please wait...").pack(pady=20)
        self.loading_progress = tk.Label(self.loading_window, text="0%")
        self.loading_progress.pack()
        
        self.loading_window.grab_set()
        self.root.update()

    # Mengupdate progres loading
    def update_loading_screen(self, progress):
        if hasattr(self, 'loading_window'):
            self.loading_progress.config(text=f"{progress}%")
            self.loading_window.update()

    # Menutup layar loading
    def hide_loading_screen(self):
        if hasattr(self, 'loading_window'):
            self.loading_window.grab_release()
            self.loading_window.destroy()

    # Memuat peta default (jalur persegi panjang)
    def load_default_map(self):
        img = Image.new("RGB", (1000, 700), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 900, 600], fill=self.road_color)
        self.process_map(img)

    # Memuat peta custom dari file gambar
    def load_custom_map(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
        if path:
            try:
                self.show_loading_screen()
                for i in range(1, 6):
                    time.sleep(0.1)
                    self.update_loading_screen(i * 20)
                img = Image.open(path)
                if img.size != (1000, 700):
                    img = img.resize((1000, 700), Image.LANCZOS)
                self.process_map(img)
                self.update_loading_screen(100)
                time.sleep(0.2)
                self.hide_loading_screen()
            except Exception as e:
                self.hide_loading_screen()
                messagebox.showerror("Error", str(e))

    # Proses gambar dan deteksi piksel jalan
    def process_map(self, img):
        self.track_image = img.convert("RGB")
        self.tk_image = ImageTk.PhotoImage(self.track_image)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        
        width, height = img.size
        self.track_pixels = []
        
        total_pixels = width * height
        update_interval = total_pixels // 10
        
        for x in range(width):
            for y in range(height):
                if self.track_image.getpixel((x, y)) == self.road_color:
                    self.track_pixels.append((x, y))
                if (x * height + y) % update_interval == 0:
                    progress = ((x * height + y) / total_pixels) * 100
                    self.update_loading_screen(int(progress))
        
        self.reset()

    # Cek apakah posisi berada di jalan
    def is_on_road(self, pos):
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self.track_image.width and 0 <= y < self.track_image.height:
            return self.track_image.getpixel((x, y)) == self.road_color
        return False

    # Fungsi pathfinding menggunakan algoritma A*
    def calculate_path(self):
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
        return []

    # Sensor mobil untuk mendeteksi sekitar (8 arah)
    def sense_environment(self):
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
                readings.append(0 if pixel == self.road_color else 1)
            else:
                readings.append(1)
        return readings

    # Pengambilan keputusan arah berdasarkan pathfinding atau obstacle
    def decide_direction(self, readings):
        if self.pathfinding_var.get() and not self.path:
            self.path = self.calculate_path()
        if self.pathfinding_var.get() and self.path:
            next_pos = self.path[0]
            dx = next_pos[0] - self.car_pos[0]
            dy = next_pos[1] - self.car_pos[1]
            target_angle = math.atan2(dy, dx)
            if math.hypot(dx, dy) < 10:
                self.path.pop(0)
            angle_diff = (target_angle - self.car_angle + math.pi) % (2*math.pi) - math.pi
            max_steering = math.pi/6
            return self.car_angle + max(-max_steering, min(max_steering, angle_diff))
        front_readings = readings[:5]
        if any(r == 1 for r in front_readings[:3]):
            self.avoidance_mode = True
        if self.avoidance_mode:
            if all(r == 0 for r in front_readings[:3]):
                self.avoidance_mode = False
            else:
                if readings[3] == 0:
                    return self.car_angle - math.pi/8
                elif readings[4] == 0:
                    return self.car_angle + math.pi/8
                else:
                    return self.car_angle + math.pi
        dx = self.target_pos[0] - self.car_pos[0]
        dy = self.target_pos[1] - self.car_pos[1]
        target_angle = math.atan2(dy, dx)
        angle_diff = (target_angle - self.car_angle + math.pi) % (2*math.pi) - math.pi
        max_steering = math.pi/8
        return self.car_angle + max(-max_steering, min(max_steering, angle_diff))

    # Fungsi untuk menggerakkan mobil
    def move_car(self):
        if not self.is_moving:
            return
        readings = self.sense_environment()
        self.car_angle = self.decide_direction(readings)
        front_clear = all(r == 0 for r in readings[:3])
        self.speed = 5 if front_clear else 2
        direction = (math.cos(self.car_angle), math.sin(self.car_angle))
        self.car_pos[0] += direction[0] * self.speed
        self.car_pos[1] += direction[1] * self.speed
        self.draw()
        if math.hypot(self.target_pos[0]-self.car_pos[0], self.target_pos[1]-self.car_pos[1]) < 20:
            self.is_moving = False
            messagebox.showinfo("Arrived", "Target reached successfully!")
            return
        self.root.after(30, self.move_car)

    # Menggambar ulang canvas
    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        if self.pathfinding_var.get() and self.path:
            for i in range(len(self.path)-1):
                self.canvas.create_line(self.path[i][0], self.path[i][1], 
                                      self.path[i+1][0], self.path[i+1][1],
                                      fill="blue", width=2)
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
        target_size = 20
        self.canvas.create_oval(
            self.target_pos[0]-target_size, self.target_pos[1]-target_size,
            self.target_pos[0]+target_size, self.target_pos[1]+target_size,
            fill="green", outline="black"
        )

    # Mulai simulasi
    def start(self):
        if not self.is_moving:
            self.is_moving = True
            self.path = self.calculate_path() if self.pathfinding_var.get() else []
            self.move_car()

    # Hentikan gerakan mobil
    def stop(self):
        self.is_moving = False

    # Reset posisi dan status
    def reset(self):
        self.stop()
        self.car_pos = [100, 100]
        self.target_pos = [300, 300]
        self.car_angle = 0
        self.collisions = 0
        self.path = []
        self.collision_label.config(text="Border Crossings: 0")
        self.draw()

    # Acak posisi mobil dan target
    def randomize_positions(self):
        if self.track_pixels:
            self.car_pos = list(random.choice(self.track_pixels))
            valid = [p for p in self.track_pixels if math.dist(p, self.car_pos) > 100]
            if valid:
                self.target_pos = list(random.choice(valid))
            self.path = self.calculate_path() if self.pathfinding_var.get() else []
            self.draw()

# Jalankan program jika file ini dijalankan langsung
if __name__ == "__main__":
    root = tk.Tk()
    app = SelfDrivingCarSimulator(root)
    root.mainloop()
