# ✈️ AeroZeka - Yapay Zeka Destekli Filo Atama Optimizasyonu

AeroZeka, havayolu şirketlerinin kârlılığını maksimize etmek için geliştirilmiş, makine öğrenmesi destekli bir **Filo Atama (Fleet Assignment)** masaüstü uygulamasıdır. Kullanıcının girdiği uçuş rotasına göre tahmini yolcu talebini hesaplar ve Türk Hava Yolları (THY) filosu içerisinden en uygun uçağı (kapasite, menzil ve yakıt tüketimi parametreleriyle) o sefere atar.

## 🚀 Öne Çıkan Özellikler

* **🤖 Makine Öğrenmesi ile Talep Tahmini:** Basit rastgele atamalar yerine, uçuş mesafesi ve mevsimsel verilere dayalı olarak `RandomForestRegressor` modeli ile uçuşun tahmini yolcu sayısını öngörür.
* **🌍 Dinamik Harita ve Rota Çizimi:** `tkintermapview` entegrasyonu ile kalkış ve varış noktalarını harita üzerinde pinler, kıtalararası uçuşların rotasını çizer ve otomatik odaklanma yapar.
* **🛡️ Fallback (Yedek) Mekanizması:** API o anki canlı uçuşu bulamasa bile, dahili havalimanı koordinat sözlüğü ve `geopy` sayesinde mesafeyi kendisi hesaplar, sistemin çökmesini engeller (Bulletproof Architecture).
* **✈️ Gerçekçi Filo ve Menzil Kontrolü:** Airbus A350, Boeing 787 Dreamliner gibi geniş gövdeli uçakları içeren THY filo verisiyle çalışır. Uçakları sadece kapasiteye göre değil, maksimum uçuş menziline (Range) göre de filtreler.
* **🎨 Modern UI/UX:** `customtkinter` ile geliştirilmiş; koyu tema (Dark Mode) destekli, akıcı, modüler ve kullanıcı dostu arayüz.

## 🛠️ Kullanılan Teknolojiler

* **Dil:** Python 3.x
* **Arayüz (GUI):** CustomTkinter, tkintermapview, Pillow (PIL)
* **Makine Öğrenmesi:** Scikit-Learn, Pandas, NumPy, Joblib
* **Veri ve Haritalama:** FlightRadarAPI (Uçuş Verisi), Geopy (Mesafe Hesaplama)

## ⚙️ Kurulum ve Çalıştırma

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

1. **Repoyu Klonlayın:**
   ```bash
   git clone https://github.com/onurakyuz61/aerozeka-fleet-optimization.git
   cd aerozeka-fleet-optimization
   ```

2. **Gerekli Kütüphaneleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Opsiyonel) Makine Öğrenmesi Modelini Eğitin:**  
   Eğer `demand_model.pkl` dosyası mevcut değilse, önce modeli eğitmeniz gerekir:
   ```bash
   python ml/train_demand_model.py
   ```

4. **Uygulamayı Başlatın:**
   ```bash
   python main.py
   ```

## 💡 Nasıl Çalışır? (Optimizasyon Algoritması)

Kullanıcı bir rota (Örn: IST-JFK) girdiğinde sistem şu adımları izler:

1. Rota koordinatlarını ve mesafesini bulur (~8047 km).
2. ML modeli bu mesafedeki bir uçuş için beklenen yolcu sayısını tahmin eder (Örn: 175 yolcu).
3. Algoritma menzili 8047 km'den kısa olan dar gövdeli uçakları (örn: A320) eler.
4. Kalan geniş gövdeli uçaklar (örn: A350, B787) arasından, tahmin edilen 175 yolcuyu karşılayacak kapasitede olup en düşük yakıt tüketimine sahip olanı **"En Karlı Seçim"** olarak belirler.

---

**Geliştirici:** Onur Akyüz  

Bu proje, modern yazılım mimarisi, makine öğrenmesi ve UI/UX prensipleri kullanılarak geliştirilmiştir.
