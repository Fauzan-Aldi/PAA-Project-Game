import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import random
import math
import heapq

class SimulatorMobilSelfDriving:
    def __init__(self, root):
        # Inisialisasi aplikasi simulator
        self.root = root
        self.root.title("Simulator Mobil Self-Driving")
        
        # Definisi warna yang digunakan dalam simulasi
        self.warna_jalan = (90, 90, 90)       # Warna abu-abu untuk jalan
        self.warna_pinggir = (255, 255, 255)  # Warna putih untuk pinggiran jalan
        self.warna_target = (0, 255, 0)       # Warna hijau untuk target
        
        # Inisialisasi status mobil
        self.posisi_mobil = [100, 100]        # Posisi awal mobil
        self.posisi_target = [300, 300]       # Posisi target yang harus dicapai
        self.sedang_bergerak = False          # Status pergerakan mobil
        self.kecepatan = 3                    # Kecepatan awal mobil
        self.sudut_mobil = 0                  # Arah hadap mobil (dalam radian)
        self.jumlah_tabrakan = 0              # Jumlah tabrakan atau pelanggaran batas
        self.pixel_jalan = []                 # Menyimpan koordinat piksel jalan yang valid
        
        # Variabel untuk peningkatan AI
        self.posisi_terlewati = []            # Menyimpan posisi yang sudah dilewati mobil
        self.mode_menghindar = False          # Status mode menghindar rintangan
        self.jalur = []                       # Menyimpan jalur hasil pencarian dengan A*
        
        # Siapkan antarmuka pengguna
        self.buat_widget()
        self.muat_peta_default()

    def buat_widget(self):
        # Membuat elemen UI untuk simulator
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        # Tombol-tombol kontrol
        tk.Button(frame, text="Muat Peta Default", command=self.muat_peta_default).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Muat Peta Kustom", command=self.muat_peta_kustom).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Mulai", command=self.mulai).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Berhenti", command=self.berhenti).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Acak Posisi", command=self.acak_posisi).pack(side=tk.LEFT, padx=5)
        
        # Checkbox untuk mengaktifkan/menonaktifkan pencarian jalur
        self.var_pencarian_jalur = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Gunakan Pencarian Jalur", variable=self.var_pencarian_jalur).pack(side=tk.LEFT, padx=5)

        # Canvas untuk menampilkan simulasi
        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()

        # Label untuk menampilkan jumlah pelanggaran
        self.label_tabrakan = tk.Label(self.root, text="Pelanggaran Batas: 0")
        self.label_tabrakan.pack()

    def tampilkan_loading(self):
        """Menampilkan layar loading saat memproses peta"""
        self.loading_screen = tk.Toplevel(self.root)
        self.loading_screen.title("Memproses Peta")
        self.loading_screen.geometry("300x100")
        self.loading_screen.resizable(False, False)
        
        # Pusatkan window loading relatif terhadap window utama
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 50
        self.loading_screen.geometry(f"+{x}+{y}")
        
        # Komponen UI untuk layar loading
        tk.Label(self.loading_screen, text="Sedang memproses peta...").pack(pady=10)
        self.progress = tk.Label(self.loading_screen, text="0%")
        self.progress.pack()
        
        # Progress bar sederhana
        self.progress_bar = tk.Canvas(self.loading_screen, width=250, height=20, bg="white")
        self.progress_bar.pack()
        self.progress_bar.create_rectangle(0, 0, 0, 20, fill="blue", tags="progress")
        
        self.loading_screen.grab_set()  # Jadikan modal dialog
        self.root.update()

    def perbarui_loading(self, persentase):
        """Memperbarui tampilan progress pada layar loading"""
        if hasattr(self, 'loading_screen'):
            self.progress_bar.coords("progress", 0, 0, 250 * (persentase/100), 20)
            self.progress.config(text=f"{persentase}%")
            self.loading_screen.update()

    def sembunyikan_loading(self):
        """Menghilangkan layar loading setelah selesai proses"""
        if hasattr(self, 'loading_screen'):
            self.loading_screen.grab_release()
            self.loading_screen.destroy()
            del self.loading_screen

    def muat_peta_default(self):
        """Membuat peta default berupa kotak sederhana"""
        img = Image.new("RGB", (800, 600), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 700, 500], fill=self.warna_jalan, outline=self.warna_pinggir, width=10)
        self.proses_peta_dengan_loading(img)

    def muat_peta_kustom(self):
        """Memuat peta dari file gambar yang dipilih pengguna"""
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
        """Proses gambar peta dan identifikasi area jalan dengan indikator loading"""
        self.gambar_jalan = img.convert("RGB")
        self.tk_gambar = ImageTk.PhotoImage(self.gambar_jalan)
        self.canvas.create_image(0, 0, image=self.tk_gambar, anchor=tk.NW)
        
        # Scan seluruh gambar untuk mengidentifikasi piksel jalan
        lebar, tinggi = img.size
        self.pixel_jalan = []
        total_pixel = lebar * tinggi
        pixel_diproses = 0
        
        for x in range(lebar):
            for y in range(tinggi):
                if self.gambar_jalan.getpixel((x, y)) == self.warna_jalan:
                    self.pixel_jalan.append((x, y))
                
                # Update progress setiap 1000 pixel untuk mengurangi lag
                pixel_diproses += 1
                if pixel_diproses % 1000 == 0:
                    persentase = 30 + int((pixel_diproses / total_pixel) * 70)
                    self.perbarui_loading(persentase)
        
        self.reset()
        self.perbarui_loading(100)

    def apakah_di_jalan(self, pos):
        """Memeriksa apakah posisi tertentu berada di jalan"""
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self.gambar_jalan.width and 0 <= y < self.gambar_jalan.height:
            return self.gambar_jalan.getpixel((x, y)) == self.warna_jalan
        return False

    def hitung_jalur(self):
        """Algoritma A* untuk mencari jalur optimal dari posisi mobil ke target"""
        def heuristik(a, b):
            # Heuristik Manhattan distance
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        awal = (int(self.posisi_mobil[0]), int(self.posisi_mobil[1]))
        tujuan = (int(self.posisi_target[0]), int(self.posisi_target[1]))
        
        # Arah pergerakan (8 arah: vertikal, horizontal, diagonal)
        tetangga = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        set_tertutup = set()  # Node yang sudah dievaluasi
        asal = {}             # Menyimpan node asal untuk rekonstruksi jalur
        skor_g = {awal:0}     # Biaya dari awal ke node ini
        skor_f = {awal:heuristik(awal, tujuan)}  # Estimasi total biaya
        heap = []             # Priority queue untuk A*
        
        heapq.heappush(heap, (skor_f[awal], awal))
        
        while heap:
            sekarang = heapq.heappop(heap)[1]
            
            # Jika sudah mencapai tujuan, rekonstruksi jalur
            if sekarang == tujuan:
                jalur = []
                while sekarang in asal:
                    jalur.append(sekarang)
                    sekarang = asal[sekarang]
                return jalur[::-1]  # Balik jalur
                
            set_tertutup.add(sekarang)
            for i, j in tetangga:
                tetangga_pos = sekarang[0] + i, sekarang[1] + j
                # Cek apakah tetangga dalam batas gambar
                if 0 <= tetangga_pos[0] < self.gambar_jalan.width and 0 <= tetangga_pos[1] < self.gambar_jalan.height:
                    # Cek apakah tetangga berada di jalan
                    if self.gambar_jalan.getpixel(tetangga_pos) != self.warna_jalan:
                        continue
                        
                    skor_g_sementara = skor_g[sekarang] + heuristik(sekarang, tetangga_pos)
                    
                    # Skip jika sudah ada jalur lebih baik ke node ini
                    if tetangga_pos in set_tertutup and skor_g_sementara >= skor_g.get(tetangga_pos, float('inf')):
                        continue
                        
                    # Jika ini jalur lebih baik, rekam
                    if skor_g_sementara < skor_g.get(tetangga_pos, float('inf')) or tetangga_pos not in [i[1] for i in heap]:
                        asal[tetangga_pos] = sekarang
                        skor_g[tetangga_pos] = skor_g_sementara
                        skor_f[tetangga_pos] = skor_g_sementara + heuristik(tetangga_pos, tujuan)
                        heapq.heappush(heap, (skor_f[tetangga_pos], tetangga_pos))
        
        return []  # Jalur tidak ditemukan

    def sensor_lingkungan(self):
        """Implementasi sensor jarak 8 arah untuk deteksi rintangan"""
        jangkauan_sensor = 30  # Jarak sensor dalam piksel
        # Sudut penempatan sensor (relatif terhadap arah mobil)
        sudut_sensor = [0, -math.pi/4, math.pi/4, -math.pi/2, math.pi/2, 
                       -math.pi/8, math.pi/8, -3*math.pi/4, 3*math.pi/4]
        pembacaan = []

        for sudut in sudut_sensor:
            sudut_total = self.sudut_mobil + sudut
            # Hitung ujung sensor
            x = int(self.posisi_mobil[0] + math.cos(sudut_total) * jangkauan_sensor)
            y = int(self.posisi_mobil[1] + math.sin(sudut_total) * jangkauan_sensor)
            
            # Periksa jenis permukaan pada ujung sensor
            if 0 <= x < self.gambar_jalan.width and 0 <= y < self.gambar_jalan.height:
                pixel = self.gambar_jalan.getpixel((x, y))
                if pixel == self.warna_pinggir:
                    pembacaan.append(1)  # Terdeteksi pinggir jalan
                elif pixel == self.warna_jalan:
                    pembacaan.append(0)  # Jalan normal
                else:
                    pembacaan.append(2)  # Di luar jalan
            else:
                pembacaan.append(2)  # Keluar batas gambar
                
        return pembacaan

    def tentukan_arah(self, pembacaan):
        """Logika pengambilan keputusan untuk menentukan arah gerak mobil"""
        # Jika pencarian jalur aktif dan jalur belum dihitung
        if self.var_pencarian_jalur.get() and not self.jalur:
            self.jalur = self.hitung_jalur()
        
        # Jika menggunakan pencarian jalur dan jalur tersedia
        if self.var_pencarian_jalur.get() and self.jalur:
            # Ambil titik berikutnya pada jalur
            pos_berikutnya = self.jalur[0]
            dx = pos_berikutnya[0] - self.posisi_mobil[0]
            dy = pos_berikutnya[1] - self.posisi_mobil[1]
            sudut_target = math.atan2(dy, dx)
            
            # Hapus titik dari jalur jika sudah cukup dekat
            if math.hypot(dx, dy) < 10:
                self.jalur.pop(0)
                
            # Batas seberapa cepat mobil dapat berbelok
            selisih_sudut = (sudut_target - self.sudut_mobil + math.pi) % (2*math.pi) - math.pi
            maksimal_belok = math.pi/6  # Maksimal belok 30 derajat
            return self.sudut_mobil + max(-maksimal_belok, min(maksimal_belok, selisih_sudut))
        
        # Logika menghindar rintangan
        pembacaan_depan = pembacaan[:5]  # Sensor yang menghadap depan
        if any(r == 1 for r in pembacaan_depan[:3]):  # Ada rintangan di depan
            self.mode_menghindar = True
            
        if self.mode_menghindar:
            # Keluar dari mode menghindar jika jalan di depan sudah aman
            if all(r == 0 for r in pembacaan_depan[:3]):
                self.mode_menghindar = False
            else:
                # Strategi menghindar: coba belok kiri dulu, baru kanan
                if pembacaan[3] == 0:  # Kiri kosong
                    return self.sudut_mobil - math.pi/8
                elif pembacaan[4] == 0:  # Kanan kosong
                    return self.sudut_mobil + math.pi/8
                else:
                    return self.sudut_mobil + math.pi  # Putar balik jika terjebak
        
        # Default: arahkan langsung ke target
        dx = self.posisi_target[0] - self.posisi_mobil[0]
        dy = self.posisi_target[1] - self.posisi_mobil[1]
        sudut_target = math.atan2(dy, dx)
        
        # Batasi sudut belok maksimal untuk gerakan lebih alami
        selisih_sudut = (sudut_target - self.sudut_mobil + math.pi) % (2*math.pi) - math.pi
        maksimal_belok = math.pi/8  # Maksimal belok 22.5 derajat
        return self.sudut_mobil + max(-maksimal_belok, min(maksimal_belok, selisih_sudut))

    def gerakkan_mobil(self):
        """Fungsi rekursif untuk mengontrol pergerakan mobil setiap frame"""
        if not self.sedang_bergerak:
            return
            
        # Dapatkan pembacaan sensor dan tentukan arah
        pembacaan = self.sensor_lingkungan()
        self.sudut_mobil = self.tentukan_arah(pembacaan)
        
        # Atur kecepatan berdasar kondisi di depan (lebih cepat jika jalan bebas)
        depan_jelas = all(r == 0 for r in pembacaan[:3])
        self.kecepatan = 5 if depan_jelas else 2
        
        # Hitung pergerakan berdasar arah dan kecepatan
        arah = (math.cos(self.sudut_mobil), math.sin(self.sudut_mobil))
        self.posisi_mobil[0] += arah[0] * self.kecepatan
        self.posisi_mobil[1] += arah[1] * self.kecepatan
        
        # Lacak pelanggaran batas jalan
        if not self.apakah_di_jalan(self.posisi_mobil):
            self.jumlah_tabrakan += 1
            self.label_tabrakan.config(text=f"Pelanggaran Batas: {self.jumlah_tabrakan}")
        
        # Perbarui tampilan
        self.gambar()
        
        # Cek apakah sudah mencapai target
        if math.hypot(self.posisi_target[0]-self.posisi_mobil[0], self.posisi_target[1]-self.posisi_mobil[1]) < 20:
            self.sedang_bergerak = False
            messagebox.showinfo("Sampai", "Target berhasil dicapai!")
            return
            
        # Jadwalkan frame berikutnya (30ms = ~33 FPS)
        self.root.after(30, self.gerakkan_mobil)

    def gambar(self):
        """Menggambar semua elemen visual pada canvas"""
        self.canvas.delete("all")  # Hapus semua item sebelumnya
        self.canvas.create_image(0, 0, image=self.tk_gambar, anchor=tk.NW)
        
        # Gambar jalur jika tersedia dan diaktifkan
        if self.var_pencarian_jalur.get() and self.jalur:
            for i in range(len(self.jalur)-1):
                self.canvas.create_line(self.jalur[i][0], self.jalur[i][1], 
                                      self.jalur[i+1][0], self.jalur[i+1][1],
                                      fill="blue", width=2)
        
        # Gambar mobil sebagai segitiga untuk menunjukkan arah
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
        
        # Gambar target sebagai lingkaran hijau
        ukuran_target = 20
        self.canvas.create_oval(
            self.posisi_target[0]-ukuran_target, self.posisi_target[1]-ukuran_target,
            self.posisi_target[0]+ukuran_target, self.posisi_target[1]+ukuran_target,
            fill="green", outline="black"
        )

    def mulai(self):
        """Memulai simulasi pergerakan mobil"""
        if not self.sedang_bergerak:
            self.sedang_bergerak = True
            # Hitung jalur jika opsi pencarian jalur diaktifkan
            self.jalur = self.hitung_jalur() if self.var_pencarian_jalur.get() else []
            self.gerakkan_mobil()

    def berhenti(self):
        """Menghentikan simulasi pergerakan mobil"""
        self.sedang_bergerak = False

    def reset(self):
        """Mengembalikan simulasi ke kondisi awal"""
        self.berhenti()
        self.posisi_mobil = [100, 100]
        self.posisi_target = [300, 300]
        self.sudut_mobil = 0
        self.jumlah_tabrakan = 0
        self.jalur = []
        self.label_tabrakan.config(text="Pelanggaran Batas: 0")
        self.gambar()

    def acak_posisi(self):
        """Mengacak posisi awal mobil dan target pada area jalan yang valid"""
        if self.pixel_jalan:
            # Pilih posisi mobil secara acak dari piksel jalan
            self.posisi_mobil = list(random.choice(self.pixel_jalan))
            # Pastikan target cukup jauh dari mobil (minimal 100 piksel)
            valid = [p for p in self.pixel_jalan if math.dist(p, self.posisi_mobil) > 100]
            if valid:
                self.posisi_target = list(random.choice(valid))
            # Hitung ulang jalur jika pencarian jalur diaktifkan
            self.jalur = self.hitung_jalur() if self.var_pencarian_jalur.get() else []
            self.gambar()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulatorMobilSelfDriving(root)
    root.mainloop()
