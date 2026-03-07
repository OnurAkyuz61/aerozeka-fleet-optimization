import random
import time
import math
import logging

# Loglama ayarları
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    from FlightRadar24 import FlightRadar24API
    HAS_FLIGHTRADAR = True
except ImportError:
    HAS_FLIGHTRADAR = False
    logging.warning("FlightRadar24 kütüphanesi bulunamadı! 'pip install FlightRadarAPI' komutu ile kurabilirsiniz.")
    logging.warning("Sistem simülasyon/mock verileri ile çalışmaya devam edecektir.")

class FlightDataFetcher:
    """
    FlightDataFetcher sınıfı, gerçek zamanlı uçuş verilerini çekmek ve eksik kısımları
    simüle etmek için oluşturulmuştur. Dış API'lere erişim sağlar.
    """

    def __init__(self):
        """
        Sınıf başlatılırken eğer FlightRadar24 kütüphanesi mevcutsa API istemcisi oluşturulur.
        """
        self.api = FlightRadar24API() if HAS_FLIGHTRADAR else None
        
        # Simülasyon verileri için bilinen bazı modellerin kapasite limitleri
        self.capacity_limits = {
            "B738": (150, 189),
            "A320": (140, 180),
            "A321": (180, 230),
            "B777": (300, 396),
            "A330": (250, 300),
            # Bilinmeyen modeller için varsayılan bir limit
            "DEFAULT": (100, 200)
        }

    def fetch_flight_data(self, flight_number: str) -> dict:
        """
        Verilen uçuş numarası için (Örn: 'TK2828') mesafeyi ve uçak modelini getirir.
        Gerçek API erişimi varsa kullanır, aksi halde ya da uçuş bulunamazsa mock veri döner.

        Args:
            flight_number (str): Sorgulanacak uçuş numarası.

        Returns:
            dict: Uçuş bilgilerini içeren sözlük (mesafe(km), uçak_modeli, tahmini_yolcu).
        """
        logging.info(f"{flight_number} uçuşu için veri aranıyor...")
        
        distance_km = 0.0
        aircraft_code = "B738" # Varsayılan uçak modeli
        
        # Eğer kütüphane yüklüyse gerçek veriyi çekmeyi dene
        if self.api:
            try:
                flights = self.api.get_flights(flight=flight_number)
                if flights:
                    flight = flights[0] # İlk bulunan uçuş nesnesi
                    # Detaylı bilgi almak için
                    flight_details = self.api.get_flight_details(flight)
                    
                    aircraft_code = flight_details.get("aircraft", {}).get("model", {}).get("code", "B738")
                    
                    # Havalimanı koordinatları üzerinden mesafe hesaplama (HaverSine Formülü vs.)
                    # FlightRadar API'sinde doğrudan distance gelmeyebilir, origin ve destination koordinatlarını alalım.
                    airport_origin = flight_details.get("airport", {}).get("origin", {}).get("position", {})
                    airport_dest = flight_details.get("airport", {}).get("destination", {}).get("position", {})
                    
                    lat1 = airport_origin.get("latitude")
                    lon1 = airport_origin.get("longitude")
                    lat2 = airport_dest.get("latitude")
                    lon2 = airport_dest.get("longitude")
                    
                    if lat1 and lon1 and lat2 and lon2:
                        distance_km = self._calculate_haversine(lat1, lon1, lat2, lon2)
                    else:
                        distance_km = self._mock_distance()
                else:
                    logging.warning(f"'{flight_number}' için aktif uçuş bulunamadı. Mock veri üretiliyor.")
                    distance_km = self._mock_distance()
                    aircraft_code = "A320" # Mock için alternatif model
                    
            except Exception as e:
                logging.error(f"API sorgusunda hata: {e}. Mock veri kullanılacak.")
                distance_km = self._mock_distance()
        else:
            # FlightRadar kütüphanesi yüklü değilse tamamen mock veri döner
            distance_km = self._mock_distance()
        
        # Mesafeyi yuvarlayalım
        distance_km = round(distance_km, 2)
        
        # Yolcu sayısını model bağımlı olarak simüle edelim
        passenger_count = self._simulate_passenger_count(aircraft_code)
        
        result = {
            "flight_number": flight_number,
            "distance_km": distance_km,
            "aircraft_model": aircraft_code,
            "estimated_passenger": passenger_count
        }
        
        logging.info(f"Veri çekimi başarılı: {result}")
        return result

    def _simulate_passenger_count(self, aircraft_model: str) -> int:
        """
        Verilen uçak modelinin kapasite limitlerine göre tahmini ve mantıklı bir yolcu sayısı üretir.

        Args:
            aircraft_model (str): Uçak modeli (Örn: 'B738', 'A320').

        Returns:
            int: Simüle edilmiş rastgele yolcu sayısı.
        """
        # Modelin sözlükte olup olmadığını kontrol et, yoksa DEFAULT limitleri kullan
        min_pax, max_pax = self.capacity_limits.get(aircraft_model, self.capacity_limits["DEFAULT"])
        
        # Kapasitenin %70 ile %100'ü arasında bir doluluk oranı simülasyonu
        # Rastgelelik katıyoruz ki gerçekçi olsun
        simulated_count = random.randint(int(max_pax * 0.70), max_pax)
        return simulated_count

    def _calculate_haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        İki dünya koordinatı arasındaki mesafeyi Haversine formülü ile km cinsinden hesaplar.
        """
        R = 6371.0 # Dünya yarıçapı (km)
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2)**2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def _mock_distance(self) -> float:
        """
        API hatası veya ulaşılamaması durumunda örnek bir uçuş mesafesi döner.
        """
        return random.uniform(300.0, 3500.0)

if __name__ == "__main__":
    # Test amaçlı kendi başına çalıştırıldığında test verisi üretir
    fetcher = FlightDataFetcher()
    data = fetcher.fetch_flight_data("TK2828")
    print(data)
