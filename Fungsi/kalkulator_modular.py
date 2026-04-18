def hitung_redaman(jarak_km, jumlah_splicing):
    redaman_kabel = jarak_km * 0.35
    redaman_splicing = jumlah_splicing * 0.1
    total_redaman = redaman_kabel + redaman_splicing
    return total_redaman

hasil_jalur_a = hitung_redaman(5, 4)
hasil_jalur_b = hitung_redaman(2.5, 2)

print(f"hasil redaman yang dihasilkan oleh jalur A adalah {hasil_jalur_a} dB, sedangkan untuk jalur B adalah {hasil_jalur_b} dB")