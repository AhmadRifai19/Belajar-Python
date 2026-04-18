jarak_km = float(input("Masukkan panjang kabel dalam km: "))
jumlah_splicing = int(input("Masukkan jumlah titik splicing: "))

redaman_kabel = jarak_km * 0.35
redaman_splicing = jumlah_splicing * 0.1

jumlah_redaman = redaman_kabel + redaman_splicing

print("Redaman yang dihasilkan adalah", jumlah_redaman, "Db")