'use client';

import { useState, useEffect } from 'react';

// Tipe data untuk objek Mobil dari API
interface Mobil {
  id: number;
  nama_mobil: string;
  kategori: string;
  harga_per_hari: number;
  gambar_url?: string;
}

export default function HalamanUtama() {
  const [armada, setArmada] = useState<Mobil[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  
  const [namaMobil, setNamaMobil] = useState('');
  const [kategori, setKategori] = useState('Mobil Keluarga');
  const [harga, setHarga] = useState('');
  const [gambar, setGambar] = useState<File | null>(null); // [BARU] State untuk file gambar
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    if (localStorage.getItem('token')) setIsLoggedIn(true);
    muatData();
  }, []);

  const muatData = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/mobil');
      const data = await res.json();
      setArmada(data.data_armada);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await fetch('http://127.0.0.1:8000/login', { method: 'POST', body: formData });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      setIsLoggedIn(true);
    } else {
      alert("Login Gagal!");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
  };

  const handleTambahMobil = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // [BARU] Menggunakan FormData karena kita mengirim File fisik, bukan sekadar Teks JSON
    const dataForm = new FormData();
    dataForm.append('nama_mobil', namaMobil);
    dataForm.append('kategori', kategori);
    dataForm.append('harga_per_hari', harga);
    if (gambar) {
      dataForm.append('gambar', gambar);
    }

    const res = await fetch('http://127.0.0.1:8000/tambah-mobil', {
      method: 'POST',
      // CATATAN PENTING: Jangan set 'Content-Type' saat memakai FormData, biarkan browser yang mengatur otomatis
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}` 
      },
      body: dataForm,
    });
    
    if (res.ok) {
      setNamaMobil(''); setHarga(''); setGambar(null);
      const inputGambar = document.getElementById('input-gambar') as HTMLInputElement | null;
      if (inputGambar) inputGambar.value = ""; // Mengosongkan form file
      muatData();
    } else {
      alert("Gagal menambah data!");
    }
  };

  const hapusMobil = async (id: number) => {
    if (confirm("Yakin ingin menghapus mobil ini?")) {
      const res = await fetch(`http://127.0.0.1:8000/mobil/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
      });
      if (res.ok) muatData();
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50">Memuat...</div>;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/70 border-b border-slate-200/60 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">REN<span className="text-indigo-600">MOL</span></h1>
          </div>
          {isLoggedIn ? (
            <button onClick={handleLogout} className="text-sm font-semibold text-slate-500 hover:text-red-600">Keluar</button>
          ) : (
             <form onSubmit={handleLogin} className="flex gap-2">
              <input type="text" placeholder="User" required onChange={(e) => setUsername(e.target.value)} className="border px-2 py-1 rounded" />
              <input type="password" placeholder="Pass" required onChange={(e) => setPassword(e.target.value)} className="border px-2 py-1 rounded" />
              <button type="submit" className="bg-indigo-600 text-white px-4 rounded">Masuk</button>
            </form>
          )}
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="mb-12"><h2 className="text-4xl font-black mb-3">Katalog Armada</h2></div>

        {isLoggedIn && (
          <div className="mb-12 bg-white p-8 rounded-3xl shadow-sm border border-indigo-100 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-2 h-full bg-indigo-500"></div>
            <h3 className="text-lg font-bold mb-6">➕ Tambah Unit Baru</h3>
            <form onSubmit={handleTambahMobil} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">Nama Kendaraan</label>
                <input type="text" value={namaMobil} onChange={(e) => setNamaMobil(e.target.value)} required className="w-full border px-4 py-3 rounded-xl" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">Kategori</label>
                <select value={kategori} onChange={(e) => setKategori(e.target.value)} className="w-full border px-4 py-3 rounded-xl">
                  <option value="Mobil Keluarga">Mobil Keluarga</option>
                  <option value="SUV">SUV</option>
                  <option value="City Car">City Car</option>
                  <option value="Premium">Premium</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">Harga (Rp)</label>
                <input type="number" value={harga} onChange={(e) => setHarga(e.target.value)} required className="w-full border px-4 py-3 rounded-xl" />
              </div>
              
              {/* [BARU] Input untuk Foto */}
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2">Foto Mobil</label>
                <input type="file" id="input-gambar" accept="image/*" onChange={(e) => setGambar(e.target.files?.[0] ?? null)} className="w-full border px-2 py-2.5 rounded-xl text-sm" />
              </div>

              <button type="submit" className="bg-indigo-600 text-white font-bold py-3 px-6 rounded-xl hover:bg-indigo-700">Simpan</button>
            </form>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {armada.map((mobil) => (
            <div key={mobil.id} className="group bg-white rounded-3xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between">
              
              {/* [BARU] Logika Menampilkan Gambar */}
              <div className="w-full h-48 bg-slate-100 rounded-2xl mb-4 overflow-hidden relative">
                {mobil.gambar_url ? (
                  <img src={`http://127.0.0.1:8000/${mobil.gambar_url}`} alt={mobil.nama_mobil} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl opacity-20">🚗</div>
                )}
              </div>

              <div className="px-2">
                <h2 className="text-xl font-bold">{mobil.nama_mobil}</h2>
                <span className="text-xs font-bold text-slate-500">{mobil.kategori}</span>
                <div className="pt-4 mt-2 border-t border-slate-100 flex justify-between items-end">
                  <p className="text-2xl font-black text-indigo-600">Rp {mobil.harga_per_hari.toLocaleString('id-ID')}</p>
                  {isLoggedIn && (
                    <button onClick={() => hapusMobil(mobil.id)} className="text-red-500 bg-red-50 p-2 rounded-lg">Hapus</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}