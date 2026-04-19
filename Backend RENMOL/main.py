from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- 1. KONFIGURASI DATABASE SQLITE ---
# Membuat file bernama 'renmol.db' di folder yang sama
SQLALCHEMY_DATABASE_URL = "sqlite:///./renmol.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODEL DATABASE (Cetakan untuk Gudang) ---
# Ini memberi tahu SQLite bentuk rak yang harus dibuat
class MobilDB(Base):
    __tablename__ = "mobil" # Nama tabel di database
    
    id = Column(Integer, primary_key=True, index=True) # ID otomatis (1, 2, 3...)
    nama_mobil = Column(String, index=True)
    kategori = Column(String)
    harga_per_hari = Column(Integer)
    status_tersedia = Column(Boolean, default=True)

# Perintah agar SQLAlchemy langsung membuat file renmol.db dan tabelnya
Base.metadata.create_all(bind=engine)

# --- MENGAKTIFKAN FASTAPI ---
app = FastAPI()

# --- KONFIGURASI CORS ---
# Mendaftarkan "negara" (URL) mana saja yang boleh mengakses API ini
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Biasanya digunakan oleh Vite
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Mengizinkan asal URL di atas
    allow_credentials=True,
    allow_methods=["*"],   # Mengizinkan semua metode (GET, POST, PUT, DELETE)
    allow_headers=["*"],   # Mengizinkan semua jenis header
)

# ... (Sisa kode database dan rute Anda tetap sama di bawah sini)

# --- 3. FUNGSI BANTUAN (Membuka dan Menutup Pintu Gudang) ---
def get_db():
    db = SessionLocal()
    try:
        yield db # Serahkan ke FastAPI untuk dipakai
    finally:
        db.close() # Tutup pintu gudang setelah selesai

# --- 4. SKEMA PYDANTIC (Dari materi sebelumnya) ---
class MobilBaru(BaseModel):
    nama_mobil: str
    kategori: str
    harga_per_hari: int
    status_tersedia: bool = True

# --- 5. RUTE APLIKASI KITA ---

@app.get("/mobil")
def lihat_daftar_mobil(db: Session = Depends(get_db)):
    # Kepala Gudang (db) mengambil semua barang dari tabel MobilDB
    armada = db.query(MobilDB).all()
    return {
        "pesan": "Berhasil mengambil data dari Database Permanen!",
        "data_armada": armada
    }

@app.post("/tambah-mobil")
def tambah_mobil(mobil: MobilBaru, db: Session = Depends(get_db)):
    # Mengemas data dari pengguna menjadi format Database
    mobil_baru = MobilDB(
        nama_mobil=mobil.nama_mobil,
        kategori=mobil.kategori,
        harga_per_hari=mobil.harga_per_hari,
        status_tersedia=mobil.status_tersedia
    )
    
    # Kepala Gudang menaruh barang ke kulkas (add) dan menguncinya (commit)
    db.add(mobil_baru)
    db.commit()
    db.refresh(mobil_baru) # Meminta ID yang baru saja dibuat oleh SQLite
    
    return {
        "pesan_sukses": f"Berhasil menyimpan {mobil_baru.nama_mobil} secara PERMANEN!",
        "data": mobil_baru
    }

# --- 6. RUTE UNTUK MENGUBAH DATA (PUT) ---
@app.put("/mobil/{id_mobil}")
def update_mobil(id_mobil: int, data_update: MobilBaru, db: Session = Depends(get_db)):
    # 1. Kepala Gudang mencari mobil berdasarkan ID
    mobil_yg_dicari = db.query(MobilDB).filter(MobilDB.id == id_mobil).first()
    
    # 2. Jika mobil tidak ditemukan, lemparkan error 404 (Not Found)
    if not mobil_yg_dicari:
        raise HTTPException(status_code=404, detail="Mobil tidak ditemukan di garasi.")
    
    # 3. Jika ketemu, timpa data lamanya dengan data yang baru
    mobil_yg_dicari.nama_mobil = data_update.nama_mobil
    mobil_yg_dicari.kategori = data_update.kategori
    mobil_yg_dicari.harga_per_hari = data_update.harga_per_hari
    mobil_yg_dicari.status_tersedia = data_update.status_tersedia
    
    # 4. Simpan perubahan tersebut ke Kulkas (Database)
    db.commit()
    db.refresh(mobil_yg_dicari)
    
    return {
        "pesan_sukses": f"Data mobil dengan ID {id_mobil} berhasil diperbarui!",
        "data_terbaru": mobil_yg_dicari
    }

# --- 7. RUTE UNTUK MENGHAPUS DATA (DELETE) ---
@app.delete("/mobil/{id_mobil}")
def hapus_mobil(id_mobil: int, db: Session = Depends(get_db)):
    # 1. Kepala Gudang mencari mobil berdasarkan ID
    mobil_yg_dicari = db.query(MobilDB).filter(MobilDB.id == id_mobil).first()
    
    # 2. Jika mobil tidak ditemukan, lemparkan error 404
    if not mobil_yg_dicari:
        raise HTTPException(status_code=404, detail="Mobil tidak ditemukan di garasi.")
    
    # 3. Jika ketemu, hapus mobil tersebut dari Kulkas (Database)
    db.delete(mobil_yg_dicari)
    db.commit()
    
    return {
        "pesan_sukses": f"Data mobil dengan ID {id_mobil} berhasil dihapus permanen dari sistem."
    }

# --- RUTE HALAMAN UTAMA ---
@app.get("/")
def halaman_utama():
    return {
        "pesan": "Selamat datang di API Sistem Rental Mobil RENMOL!",
        "status": "Server berjalan dengan baik. Silakan kunjungi /docs untuk dokumentasi."
    }