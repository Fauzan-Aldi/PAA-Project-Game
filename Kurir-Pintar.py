import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import random
import math
import heapq

class SimulatorMobilSelfDriving:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulator Mobil Self-Driving")
        
        # Warna
        self.warna_jalan = (90, 90, 90)
        self.warna_pinggir = (255, 255, 255)
        self.warna_target = (0, 255, 0)
        
        # Status mobil
        self.posisi_mobil = [100, 100]
        self.posisi_target = [300, 300]
        self.sedang_bergerak = False
        self.kecepatan = 3
        self.sudut_mobil = 0
        self.jumlah_tabrakan = 0
        self.pixel_jalan = []
        
        # Peningkatan AI
        self.posisi_terlewati = []
        self.mode_menghindar = False
        self.jalur = []
        
        # Setup antarmuka
        self.buat_widget()
        self.muat_peta_default()

    def buat_widget(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Button(frame, text="Muat Peta Default", command=self.muat_peta_default).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Muat Peta Kustom", command=self.muat_peta_kustom).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Mulai", command=self.mulai).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Berhenti", command=self.berhenti).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Acak Posisi", command=self.acak_posisi).pack(side=tk.LEFT, padx=5)
        
        self.var_pencarian_jalur = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Gunakan Pencarian Jalur", variable=self.var_pencarian_jalur).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()

        self.label_tabrakan = tk.Label(self.root, text="Pelanggaran Batas: 0")
        self.label_tabrakan.pack()

    def tampilkan_loading(self):
        """Menampilkan layar loading"""
        self.loading_screen = tk.Toplevel(self.root)
        self.loading_screen.title("Memproses Peta")
        self.loading_screen.geometry("300x100")
        self.loading_screen.resizable(False, False)
        
        # Pusatkan window loading
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 50
        self.loading_screen.geometry(f"+{x}+{y}")
        
        tk.Label(self.loading_screen, text="Sedang memproses peta...").pack(pady=10)
        self.progress = tk.Label(self.loading_screen, text="0%")
        self.progress.pack()
        
        # Buat progress bar sederhana
        self.progress_bar = tk.Canvas(self.loading_screen, width=250, height=20, bg="white")
        self.progress_bar.pack()
        self.progress_bar.create_rectangle(0, 0, 0, 20, fill="blue", tags="progress")
        
        self.loading_screen.grab_set()  # Modal dialog
        self.root.update()

    def perbarui_loading(self, persentase):
        """Memperbarui tampilan loading screen"""
        if hasattr(self, 'loading_screen'):
            self.progress_bar.coords("progress", 0, 0, 250 * (persentase/100), 20)
            self.progress.config(text=f"{persentase}%")
            self.loading_screen.update()

    def sembunyikan_loading(self):
        """Menghilangkan layar loading"""
        if hasattr(self, 'loading_screen'):
            self.loading_screen.grab_release()
            self.loading_screen.destroy()
            del self.loading_screen

    def muat_peta_default(self):
        img = Image.new("RGB", (800, 600), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 700, 500], fill=self.warna_jalan, outline=self.warna_pinggir, width=10)
        self.proses_peta_dengan_loading(img)

    def muat_peta_kustom(self):
        path = filedialog.askopenfilename(filetypes=[("Gambar", "*.png;*.jpg;*.jpeg")])
        if path:
            try:
                # Tampilkan loading screen
                self.tampilkan_loading()
                self.perbarui_loading(10)
                
                # Buka gambar (10-30%)
                img = Image.open(path)
                self.perbarui_loading(30)
                
                # Proses peta dengan progress simulasi
                self.proses_peta_dengan_loading(img)
                
                # Sembunyikan loading screen ketika selesai
                self.sembunyikan_loading()
                
            except Exception as e:
                if hasattr(self, 'loading_screen'):
                    self.sembunyikan_loading()
                messagebox.showerror("Error", f"Gagal memuat peta: {str(e)}")

    def proses_peta_dengan_loading(self, img):
        """Proses peta dengan progress bar"""
        self.gambar_jalan = img.convert("RGB")
        self.tk_gambar = ImageTk.PhotoImage(self.gambar_jalan)
        self.canvas.create_image(0, 0, image=self.tk_gambar, anchor=tk.NW)
        
        lebar, tinggi = img.size
        self.pixel_jalan = []
        total_pixel = lebar * tinggi
        pixel_diproses = 0
        
        for x in range(lebar):
            for y in range(tinggi):
                if self.gambar_jalan.getpixel((x, y)) == self.warna_jalan:
                    self.pixel_jalan.append((x, y))
                
                # Update progress setiap 1000 pixel untuk menghindari lag
                pixel_diproses += 1
                if pixel_diproses % 1000 == 0:
                    persentase = 30 + int((pixel_diproses / total_pixel) * 70)
                    self.perbarui_loading(persentase)
        
        self.reset()
        self.perbarui_loading(100)

    def apakah_di_jalan(self, pos):
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self.gambar_jalan.width and 0 <= y < self.gambar_jalan.height:
            return self.gambar_jalan.getpixel((x, y)) == self.warna_jalan
        return False

    def hitung_jalur(self):
        """Algoritma A* untuk mencari jalur"""
        def heuristik(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        awal = (int(self.posisi_mobil[0]), int(self.posisi_mobil[1]))
        tujuan = (int(self.posisi_target[0]), int(self.posisi_target[1]))
        
        tetangga = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        set_tertutup = set()
        asal = {}
        skor_g = {awal:0}
        skor_f = {awal:heuristik(awal, tujuan)}
        heap = []
        
        heapq.heappush(heap, (skor_f[awal], awal))
        
        while heap:
            sekarang = heapq.heappop(heap)[1]
            
            if sekarang == tujuan:
                jalur = []
                while sekarang in asal:
                    jalur.append(sekarang)
                    sekarang = asal[sekarang]
                return jalur[::-1]
                
            set_tertutup.add(sekarang)
            for i, j in tetangga:
                tetangga_pos = sekarang[0] + i, sekarang[1] + j
                if 0 <= tetangga_pos[0] < self.gambar_jalan.width and 0 <= tetangga_pos[1] < self.gambar_jalan.height:
                    if self.gambar_jalan.getpixel(tetangga_pos) != self.warna_jalan:
                        continue
                        
                    skor_g_sementara = skor_g[sekarang] + heuristik(sekarang, tetangga_pos)
                    
                    if tetangga_pos in set_tertutup and skor_g_sementara >= skor_g.get(tetangga_pos, float('inf')):
                        continue
                        
                    if skor_g_sementara < skor_g.get(tetangga_pos, float('inf')) or tetangga_pos not in [i[1] for i in heap]:
                        asal[tetangga_pos] = sekarang
                        skor_g[tetangga_pos] = skor_g_sementara
                        skor_f[tetangga_pos] = skor_g_sementara + heuristik(tetangga_pos, tujuan)
                        heapq.heappush(heap, (skor_f[tetangga_pos], tetangga_pos))
        
        return []  # Jalur tidak ditemukan

    def sensor_lingkungan(self):
        """Sensor 8 arah yang ditingkatkan"""
        jangkauan_sensor = 30
        sudut_sensor = [0, -math.pi/4, math.pi/4, -math.pi/2, math.pi/2, 
                       -math.pi/8, math.pi/8, -3*math.pi/4, 3*math.pi/4]
        pembacaan = []

        for sudut in sudut_sensor:
            sudut_total = self.sudut_mobil + sudut
            x = int(self.posisi_mobil[0] + math.cos(sudut_total) * jangkauan_sensor)
            y = int(self.posisi_mobil[1] + math.sin(sudut_total) * jangkauan_sensor)
            
            if 0 <= x < self.gambar_jalan.width and 0 <= y < self.gambar_jalan.height:
                pixel = self.gambar_jalan.getpixel((x, y))
                if pixel == self.warna_pinggir:
                    pembacaan.append(1)  # Terdeteksi pinggir jalan
                elif pixel == self.warna_jalan:
                    pembacaan.append(0)  # Jalan
                else:
                    pembacaan.append(2)  # Di luar jalan
            else:
                pembacaan.append(2)  # Keluar batas
                
        return pembacaan

    def tentukan_arah(self, pembacaan):
        """Pengambilan keputusan canggih dengan pencarian jalur"""
        if self.var_pencarian_jalur.get() and not self.jalur:
            self.jalur = self.hitung_jalur()
        
        # Jika menggunakan pencarian jalur dan jalur tersedia
        if self.var_pencarian_jalur.get() and self.jalur:
            pos_berikutnya = self.jalur[0]
            dx = pos_berikutnya[0] - self.posisi_mobil[0]
            dy = pos_berikutnya[1] - self.posisi_mobil[1]
            sudut_target = math.atan2(dy, dx)
            
            # Hapus titik yang sudah dicapai dari jalur
            if math.hypot(dx, dy) < 10:
                self.jalur.pop(0)
                
            selisih_sudut = (sudut_target - self.sudut_mobil + math.pi) % (2*math.pi) - math.pi
            maksimal_belok = math.pi/6  # Maksimal belok 30 derajat
            return self.sudut_mobil + max(-maksimal_belok, min(maksimal_belok, selisih_sudut))
        
        # Logika menghindar rintangan
        pembacaan_depan = pembacaan[:5]
        if any(r == 1 for r in pembacaan_depan[:3]):  # Ada rintangan di depan
            self.mode_menghindar = True
            
        if self.mode_menghindar:
            if all(r == 0 for r in pembacaan_depan[:3]):
                self.mode_menghindar = False
            else:
                # Lebih memilih belok kiri (aturan lalu lintas standar)
                if pembacaan[3] == 0:  # Kiri kosong
                    return self.sudut_mobil - math.pi/8
                elif pembacaan[4] == 0:  # Kanan kosong
                    return self.sudut_mobil + math.pi/8
                else:
                    return self.sudut_mobil + math.pi  # Berbalik arah
        
        # Default: menuju target
        dx = self.posisi_target[0] - self.posisi_mobil[0]
        dy = self.posisi_target[1] - self.posisi_mobil[1]
        sudut_target = math.atan2(dy, dx)
        
        selisih_sudut = (sudut_target - self.sudut_mobil + math.pi) % (2*math.pi) - math.pi
        maksimal_belok = math.pi/8  # Maksimal belok 22.5 derajat
        return self.sudut_mobil + max(-maksimal_belok, min(maksimal_belok, selisih_sudut))

    def gerakkan_mobil(self):
        if not self.sedang_bergerak:
            return
            
        pembacaan = self.sensor_lingkungan()
        self.sudut_mobil = self.tentukan_arah(pembacaan)
        
        # Kecepatan adaptif
        depan_jelas = all(r == 0 for r in pembacaan[:3])
        self.kecepatan = 5 if depan_jelas else 2
        
        arah = (math.cos(self.sudut_mobil), math.sin(self.sudut_mobil))
        self.posisi_mobil[0] += arah[0] * self.kecepatan
        self.posisi_mobil[1] += arah[1] * self.kecepatan
        
        # Lacak pelanggaran batas
        if not self.apakah_di_jalan(self.posisi_mobil):
            self.jumlah_tabrakan += 1
            self.label_tabrakan.config(text=f"Pelanggaran Batas: {self.jumlah_tabrakan}")
        
        self.gambar()
        
        # Cek apakah sudah sampai target
        if math.hypot(self.posisi_target[0]-self.posisi_mobil[0], self.posisi_target[1]-self.posisi_mobil[1]) < 20:
            self.sedang_bergerak = False
            messagebox.showinfo("Sampai", "Target berhasil dicapai!")
            return
            
        self.root.after(30, self.gerakkan_mobil)

    def gambar(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_gambar, anchor=tk.NW)
        
        # Gambar jalur jika tersedia
        if self.var_pencarian_jalur.get() and self.jalur:
            for i in range(len(self.jalur)-1):
                self.canvas.create_line(self.jalur[i][0], self.jalur[i][1], 
                                      self.jalur[i+1][0], self.jalur[i+1][1],
                                      fill="blue", width=2)
        
        # Gambar mobil (segitiga)
        ukuran_mobil = 15
        titik = [
            (self.posisi_mobil[0] + math.cos(self.sudut_mobil) * ukuran_mobil,
             self.posisi_mobil[1] + math.sin(self.sudut_mobil) * ukuran_mobil),
            (self.posisi_mobil[0] + math.cos(self.sudut_mobil + 2*math.pi/3) * ukuran_mobil,
             self.posisi_mobil[1] + math.sin(self.sudut_mobil + 2*math.pi/3) * ukuran_mobil),
            (self.posisi_mobil[0] + math.cos(self.sudut_mobil - 2*math.pi/3) * ukuran_mobil,
             self.posisi_mobil[1] + math.sin(self.sudut_mobil - 2*math.pi/3) * ukuran_mobil)
        ]
        self.canvas.create_polygon(titik, fill="blue", outline="black")
        
        # Gambar target (lingkaran besar)
        ukuran_target = 20
        self.canvas.create_oval(
            self.posisi_target[0]-ukuran_target, self.posisi_target[1]-ukuran_target,
            self.posisi_target[0]+ukuran_target, self.posisi_target[1]+ukuran_target,
            fill="green", outline="black"
        )

    def mulai(self):
        if not self.sedang_bergerak:
            self.sedang_bergerak = True
            self.jalur = self.hitung_jalur() if self.var_pencarian_jalur.get() else []
            self.gerakkan_mobil()

    def berhenti(self):
        self.sedang_bergerak = False

    def reset(self):
        self.berhenti()
        self.posisi_mobil = [100, 100]
        self.posisi_target = [300, 300]
        self.sudut_mobil = 0
        self.jumlah_tabrakan = 0
        self.jalur = []
        self.label_tabrakan.config(text="Pelanggaran Batas: 0")
        self.gambar()

    def acak_posisi(self):
        if self.pixel_jalan:
            self.posisi_mobil = list(random.choice(self.pixel_jalan))
            valid = [p for p in self.pixel_jalan if math.dist(p, self.posisi_mobil) > 100]
            if valid:
                self.posisi_target = list(random.choice(valid))
            self.jalur = self.hitung_jalur() if self.var_pencarian_jalur.get() else []
            self.gambar()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulatorMobilSelfDriving(root)
    root.mainloop()
