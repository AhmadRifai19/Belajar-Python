from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# [BARU] Impor alat Keamanan
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError

# --- KONFIGURASI KEAMANAN (JWT) ---
# [BARU] Kunci rahasia untuk mencetak tiket (Jangan beritahu siapa pun!)
SECRET_KEY = "kunci-rahasia-super-aman-renmol"
ALGORITHM = "HS256"
# [BARU] Memberitahu FastAPI di mana rute pintu masuknya
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- 1. KONFIGURASI DATABASE SQLITE ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./renmol.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MobilDB(Base):
    __tablename__ = "mobil"
    id = Column(Integer, primary_key=True, index=True)
    nama_mobil = Column(String, index=True)
    kategori = Column(String)
    harga_per_hari = Column(Integer)
    status_tersedia = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)

# --- MENGAKTIFKAN FASTAPI ---
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FUNGSI SATPAM (Memeriksa Tiket Gelang) ---
# [BARU] Fungsi ini akan dipasang di pintu-pintu VIP
def cek_admin(token: str = Depends(oauth2_scheme)):
    try:
        # Membaca isi tiket
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username != "admin_renmol":
            raise HTTPException(status_code=401, detail="Anda bukan Admin!")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Tiket Gelang tidak valid atau kedaluwarsa!")

class MobilBaru(BaseModel):
    nama_mobil: str
    kategori: str
    harga_per_hari: int
    status_tersedia: bool = True

# --- RUTE APLIKASI KITA ---

# [BARU] Rute untuk Login dan Mendapatkan Token
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Simulasi cek KTP (Username & Password)
    if form_data.username == "admin_renmol" and form_data.password == "rahasia123":
        # Cetak tiket gelang jika benar
        tiket = jwt.encode({"sub": form_data.username}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": tiket, "token_type": "bearer"}
    
    # Usir jika salah
    raise HTTPException(status_code=401, detail="Username atau Password salah!")

@app.get("/")
def halaman_utama():
    return {"pesan": "Selamat datang di API Sistem Rental Mobil RENMOL!"}

# Rute GET dibiarkan TERBUKA (Siapapun boleh melihat brosur mobil)
@app.get("/mobil")
def lihat_daftar_mobil(db: Session = Depends(get_db)):
    armada = db.query(MobilDB).all()
    return {"pesan": "Berhasil mengambil data", "data_armada": armada}

# Rute POST DIGEMBOK (Hanya admin yang boleh menambah armada)
# [BARU] Perhatikan tambahan: admin: str = Depends(cek_admin)
@app.post("/tambah-mobil")
def tambah_mobil(mobil: MobilBaru, db: Session = Depends(get_db), admin: str = Depends(cek_admin)):
    mobil_baru = MobilDB(**mobil.dict())
    db.add(mobil_baru)
    db.commit()
    db.refresh(mobil_baru)
    return {"pesan_sukses": f"Admin {admin} menambahkan {mobil_baru.nama_mobil}!", "data": mobil_baru}

# Rute PUT DIGEMBOK
@app.put("/mobil/{id_mobil}")
def update_mobil(id_mobil: int, data_update: MobilBaru, db: Session = Depends(get_db), admin: str = Depends(cek_admin)):
    mobil_yg_dicari = db.query(MobilDB).filter(MobilDB.id == id_mobil).first()
    if not mobil_yg_dicari: raise HTTPException(status_code=404, detail="Mobil tidak ditemukan.")
    
    for key, value in data_update.dict().items():
        setattr(mobil_yg_dicari, key, value)
    db.commit()
    db.refresh(mobil_yg_dicari)
    return {"pesan_sukses": f"Admin {admin} memperbarui mobil ID {id_mobil}!"}

# Rute DELETE DIGEMBOK
@app.delete("/mobil/{id_mobil}")
def hapus_mobil(id_mobil: int, db: Session = Depends(get_db), admin: str = Depends(cek_admin)):
    mobil_yg_dicari = db.query(MobilDB).filter(MobilDB.id == id_mobil).first()
    if not mobil_yg_dicari: raise HTTPException(status_code=404, detail="Mobil tidak ditemukan.")
    
    db.delete(mobil_yg_dicari)
    db.commit()
    return {"pesan_sukses": f"Admin {admin} menghapus mobil ID {id_mobil}."}