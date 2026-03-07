import logging

# Loglama ayarları
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FleetOptimizer:
    """
    FleetOptimizer sınıfı, çekilen uçuş profili ve simüle edilen yolcu sayısına en uygun uçağı
    yakıt tüketimi ve maliyet açısından seçmeyi sağlayan Açgözlü (Greedy) algoritma katmanıdır.
    """

    def __init__(self, fleet_data: dict = None):
        """
        Sınıf başlatılırken yerel filoyu barındıran örnek bir sözlük (dictionary) içeri alınır.
        
        Args:
            fleet_data (dict, optional): Kullanıcının kendi uçak filosu sözlüğü. 
                                         Eğer verilmezse varsayılan bir filo kullanılır.
        """
        if fleet_data is None:
            # Varsayılan (mock) uçak filosu: capacity = maks yolcu, fuel_per_km = km başına litre yakıt
            self.fleet = {
                "UCAK_A_B738": {"capacity": 189, "fuel_per_km": 3.12},
                "UCAK_B_A320": {"capacity": 180, "fuel_per_km": 2.95},
                "UCAK_C_B777": {"capacity": 396, "fuel_per_km": 7.50},
                "UCAK_D_A330": {"capacity": 300, "fuel_per_km": 5.80},
                "UCAK_E_E190": {"capacity": 114, "fuel_per_km": 1.90},
            }
        else:
            self.fleet = fleet_data

    def find_optimal_aircraft(self, distance: float, passenger_count: int) -> dict:
        """
        Tahmini yolcu ve uçuş mesafesine göre elde bulunan filodan, kapasitesi yeterli olan ve
        en az yakıtı tüketecek uçağı Açgözlü (Greedy) algoritma ile bulur.

        Args:
            distance (float): Uçuş mesafesi (km).
            passenger_count (int): Hedef uçuş için taşınması gereken simüle edilmiş yolcu sayısı.

        Returns:
            dict: En uygun uçak bilgisi ve tüketim detayı. Bulunamazsa None veya hata mesajı döner.
        """
        logging.info(f"Optimizasyon başlatılıyor -> Mesafe: {distance} km, Yolcu sayısı: {passenger_count}")
        
        suitable_aircrafts = {}

        # Adım 1: Filodaki uçakların kapasitesini yolcu sayısıyla kıyasla.
        for aircraft_id, specs in self.fleet.items():
            if specs["capacity"] >= passenger_count:
                suitable_aircrafts[aircraft_id] = specs
                
        if not suitable_aircrafts:
            error_msg = f"Filomuzda {passenger_count} yolcu kapasitesini karşılayacak uygun bir uçak bulunmamaktadır."
            logging.error(error_msg)
            return {"error": error_msg}

        logging.info(f"Kapasitesi yeterli uçaklar: {list(suitable_aircrafts.keys())}")

        optimal_aircraft = None
        min_fuel_consumption = float('inf')

        # Adım 2 ve 3: Uygun uçaklar içinde distance * fuel_per_km değerini hesapla ve en düşüğünü seç
        for aircraft_id, specs in suitable_aircrafts.items():
            # Açgözlü (Greedy) mantığıyla o anki en iyi yakıt tüketimine sahip olanı seçiyoruz.
            total_fuel = distance * specs["fuel_per_km"]
            
            if total_fuel < min_fuel_consumption:
                min_fuel_consumption = total_fuel
                optimal_aircraft = aircraft_id

        # Sonuç paketinin hazırlanması
        result = {
            "optimal_aircraft_id": optimal_aircraft,
            "max_capacity": self.fleet[optimal_aircraft]["capacity"],
            "fuel_per_km": self.fleet[optimal_aircraft]["fuel_per_km"],
            "total_estimated_fuel_L": round(min_fuel_consumption, 2),
            "passenger_count": passenger_count,
            "distance_km": distance
        }
        
        logging.info(f"En ideal seçim: {optimal_aircraft} (Tahmini Tüketim: {result['total_estimated_fuel_L']} L)")
        return result

if __name__ == "__main__":
    # Test amaçlı çalıştırıldığında örnek atama gösterir.
    optimizer = FleetOptimizer()
    
    # 1500 km'lik bir uçuşta 160 yolcu taşıyacağımızı varsayalım
    best_choice = optimizer.find_optimal_aircraft(distance=1500.0, passenger_count=160)
    print("Optimizasyon Sonucu:", best_choice)
