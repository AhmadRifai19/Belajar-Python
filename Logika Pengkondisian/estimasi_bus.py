waktu_tunggu = int(input("Masukkan waktu tunggu dalam menit: "))

if waktu_tunggu <= 5:
    print("Siap-siap! Bus sudah hampir tiba di lokasi.")
elif waktu_tunggu <= 15:
    print("Bus sedang dalam perjalanan, silakan menuju titik kumpul.")
else:
    print("Bus masih cukup jauh, Anda bisa menunggu di dalam area sekolah.")