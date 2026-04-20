from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError
import os
from typing import Optional 
from fastapi import File, Form, UploadFile, Depends, HTTPException
from dotenv import load_dotenv

# [PERBAIKAN 1] Import Cloudinary yang sebelumnya hilang!
import cloudinary
import cloudinary.uploader

# Memanggil brankas rahasia
load_dotenv() 

# --- KONFIGURASI DATABASE ---
# [PERBAIKAN 2] Hanya menggunakan URL yang aman dari .env, tidak ada lagi password yang tertulis manual
DATABASE_URL = os.environ.get("SUPABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MobilDB(Base):
    __tablename__ = "mobil"
    id = Column(Integer, primary_key=True, index=True)
    nama_mobil = Column(String, index=True)
    kategori = Column(String)
    harga_per_hari = Column(Integer)
    status_tersedia = Column(Boolean, default=True)
    gambar_url = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# --- KONFIGURASI CLOUDINARY ---
cloudinary.config( 
  cloud_name = os.environ.get("CLOUDINARY_NAME"), 
  api_key = os.environ.get("CLOUDINARY_API_KEY"), 
  api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
  secure = True
)

# --- KONFIGURASI KEAMANAN ---
SECRET_KEY = "kunci-rahasia-super-aman-renmol"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- PERSIAPAN FOLDER GAMBAR ---
os.makedirs("static/images", exist_ok=True)

# --- MENGAKTIFKAN FASTAPI ---
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware, allow_origins=["https://renmol-backend.vercel.app"], allow_credentials=True, 
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

@app.post("/tambah-mobil")
def tambah_mobil(
    nama_mobil: str = Form(...),
    kategori: str = Form(...),
    harga_per_hari: int = Form(...),
    gambar: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: str = Depends(cek_admin)
):
    url_gambar_tersimpan = None
    
    if gambar:
        try:
            hasil_upload = cloudinary.uploader.upload(gambar.file)
            url_gambar_tersimpan = hasil_upload.get("secure_url") 
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal upload ke Cloudinary: {str(e)}")

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

@app.put("/mobil/{id}")
def edit_mobil(
    id: int,
    nama_mobil: str = Form(...),
    kategori: str = Form(...),
    harga_per_hari: int = Form(...),
    gambar: Optional[UploadFile] = File(None), 
    db: Session = Depends(get_db),          # Menggunakan SQLAlchemy
    admin: str = Depends(cek_admin)         # Menggunakan sistem admin yang sudah Anda buat
):
    try:
        # 1. Cari mobil berdasarkan ID terlebih dahulu
        mobil_yg_diedit = db.query(MobilDB).filter(MobilDB.id == id).first()
        if not mobil_yg_diedit:
            raise HTTPException(status_code=404, detail="Mobil tidak ditemukan")

        # 2. Timpa data lama dengan data baru dari form
        mobil_yg_diedit.nama_mobil = nama_mobil
        mobil_yg_diedit.kategori = kategori
        mobil_yg_diedit.harga_per_hari = harga_per_hari

        # 3. Jika admin mengunggah gambar baru, kirim ke Cloudinary
        if gambar:
            hasil_upload = cloudinary.uploader.upload(gambar.file)
            mobil_yg_diedit.gambar_url = hasil_upload.get("secure_url")

        # 4. Simpan perubahan secara permanen ke database
        db.commit()
        db.refresh(mobil_yg_diedit)
        
        return {"pesan": "Data mobil berhasil diperbarui!", "data": mobil_yg_diedit}

    except Exception as e:
        # Cegah HTTPException 404 tertimpa oleh error 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Gagal mengedit data: {str(e)}")