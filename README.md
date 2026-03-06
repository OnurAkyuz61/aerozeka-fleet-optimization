# AeroZeka — Filo Atama

Havayolu seferleri için uygun uçak atamasını gösteren masaüstü uygulaması. Sefer numarası veya rota ile arama yapılır; kapasitesi yeterli uçaklar listelenir ve en düşük yakıt maliyetli uçak “En İdeal” olarak vurgulanır.

## Özellikler

- **Arama:** Sefer numarası (örn. `TK2828`) veya rota (örn. `IST-TZX`) ile arama
- **Sefer kartı:** Rota, mesafe ve beklenen yolcu sayısı
- **Uygun uçaklar:** Sadece kapasitesi yeten uçakların listesi (tablo)
- **En ideal seçim:** En az yakıt tüketen uçağın yeşil vurgulanması
- **Neden İdeal?:** Sistemin karar gerekçesini açıklayan metin

## Gereksinimler

- Python 3.8+
- Tkinter (Python ile birlikte gelir; Linux’ta `python3-tk` gerekebilir)

## Kurulum

```bash
git clone https://github.com/onurakyuz61/aerozeka-fleet-optimization.git
cd aerozeka-fleet-optimization
```

Ek Python paketi gerekmez; proje yalnızca standart kütüphane ve Tkinter kullanır.

## Çalıştırma

Proje kökünden:

```bash
python main.py
```

veya paket olarak:

```bash
python -m aerozeka
```

## Proje yapısı

```
aerozeka-fleet-optimization/
├── main.py              # Giriş noktası
├── requirements.txt     # Bağımlılıklar (yok; stdlib)
├── README.md
├── LICENSE
├── .gitignore
└── aerozeka/            # Ana paket
    ├── __init__.py
    ├── __main__.py      # python -m aerozeka giriş noktası
    ├── data.py          # Sefer ve uçak verileri
    ├── optimization.py  # Kapasite filtresi, ideal uçak seçimi
    └── ui.py            # Tkinter/ttk arayüzü
```

## Örnek veriler

- **Seferler:** TK2828 (IST-TZX), TK2424 (IST-ADB), TK2162 (IST-ESB), TK4002 (IST-AYT), TK2840 (IST-GZT)
- **Uçaklar:** Boeing 737-700/800/900, Airbus A319/A320neo/A321, Embraer E195

## Lisans

MIT License — ayrıntılar için `LICENSE` dosyasına bakın.
