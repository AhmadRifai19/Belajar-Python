from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError
import os
import shutil

# --- KONFIGURASI KEAMANAN ---
SECRET_KEY = "kunci-rahasia-super-aman-renmol"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- PERSIAPAN FOLDER GAMBAR ---
os.makedirs("static/images", exist_ok=True)

# --- KONFIGURASI DATABASE ---
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
    gambar_url = Column(String, nullable=True) # [BARU] Kolom untuk menyimpan link foto

Base.metadata.create_all(bind=engine)

# --- MENGAKTIFKAN FASTAPI ---
app = FastAPI()

# [BARU] Mengizinkan Next.js untuk mengakses folder static/images via URL
app.mount("/static", StaticFiles(directory="static"), name="static")

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def cek_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username != "admin_renmol":
            raise HTTPException(status_code=401, detail="Anda bukan Admin!")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Tiket tidak valid!")

# --- RUTE APLIKASI ---
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin_renmol" and form_data.password == "rahasia123":
        tiket = jwt.encode({"sub": form_data.username}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": tiket, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Username/Password salah!")

@app.get("/mobil")
def lihat_daftar_mobil(db: Session = Depends(get_db)):
    armada = db.query(MobilDB).all()
    return {"data_armada": armada}

# [BARU] Rute Tambah Mobil kini menggunakan Form() agar bisa menerima File
@app.post("/tambah-mobil")
def tambah_mobil(
    nama_mobil: str = Form(...),
    kategori: str = Form(...),
    harga_per_hari: int = Form(...),
    gambar: UploadFile = File(None), # Gambar bersifat opsional
    db: Session = Depends(get_db),
    admin: str = Depends(cek_admin)
):
    url_gambar_tersimpan = None
    
    # Jika admin mengunggah gambar, simpan ke folder static/images
    if gambar:
        lokasi_file = f"static/images/{gambar.filename}"
        with open(lokasi_file, "wb+") as file_object:
            shutil.copyfileobj(gambar.file, file_object)
        url_gambar_tersimpan = lokasi_file # Menyimpan path-nya ke database

    mobil_baru = MobilDB(
        nama_mobil=nama_mobil,
        kategori=kategori,
        harga_per_hari=harga_per_hari,
        gambar_url=url_gambar_tersimpan
    )
    
    db.add(mobil_baru)
    db.commit()
    db.refresh(mobil_baru)
    return {"pesan": "Berhasil ditambah", "data": mobil_baru}

@app.delete("/mobil/{id_mobil}")
def hapus_mobil(id_mobil: int, db: Session = Depends(get_db), admin: str = Depends(cek_admin)):
    mobil_yg_dicari = db.query(MobilDB).filter(MobilDB.id == id_mobil).first()
    if not mobil_yg_dicari: raise HTTPException(status_code=404)
    db.delete(mobil_yg_dicari)
    db.commit()
    return {"pesan": "Berhasil dihapus"}