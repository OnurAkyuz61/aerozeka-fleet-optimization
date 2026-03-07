# -*- coding: utf-8 -*-
"""
Yolcu talebi tahmini: ml/demand_model.pkl ile tahmin.
Model yoksa veya hata varsa çökme yok; mesafe bazlı fallback (mesafe * 0.12) kullanılır.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

# Proje ana dizini: aerozeka/core -> aerozeka -> proje kökü
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = _PROJECT_ROOT / "ml" / "demand_model.pkl"
FALLBACK_PASSENGERS = 150
# Model yokken tahmini yolcu: mesafe_km * FALLBACK_RATE, min-max aralığında
FALLBACK_RATE = 0.12
PAX_MIN, PAX_MAX = 40, 350


class DemandPredictor:
    """
    Eğitilmiş model ile yolcu tahmini. Model dosyası yoksa veya hata varsa
    uygulama çökmez; estimate_from_distance() ile mantıklı varsayılan döner.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self._path = Path(model_path) if model_path else MODEL_PATH
        self._model = None
        self._loaded = False
        self._load_attempted = False

    def load_model(self) -> bool:
        """
        demand_model.pkl dosyasını yükler. FileNotFoundError ve diğer hatalarda çökme yok.
        """
        if self._loaded and self._model is not None:
            return True
        if self._load_attempted:
            return False
        self._load_attempted = True
        try:
            if not self._path.is_file():
                raise FileNotFoundError(f"Model dosyası bulunamadı: {self._path}")
            import joblib
            self._model = joblib.load(self._path)
            self._loaded = True
            return True
        except FileNotFoundError:
            print("Lütfen önce modeli eğitin: python -m ml.train_demand_model")
            return False
        except Exception as e:
            print(f"Model yüklenemedi: {e}. Mesafe bazlı yedek kullanılacak.")
            return False

    def predict(
        self,
        distance_km: float,
        date: Optional[datetime] = None,
    ) -> Optional[int]:
        """
        Model varsa tahmini yolcu döndürür; yoksa None (caller fallback kullanır).
        """
        if not self.load_model() or self._model is None:
            return None
        when = date or datetime.now()
        ay = when.month
        haftanin_gunu = when.weekday()
        tatil_mi = 1 if haftanin_gunu >= 5 else 0
        try:
            import numpy as np
            X = np.array([[distance_km, ay, haftanin_gunu, tatil_mi]])
            pred = self._model.predict(X)
            return int(round(float(pred[0])))
        except Exception:
            return None

    @staticmethod
    def fallback_passengers() -> int:
        """Sabit yedek yolcu sayısı."""
        return FALLBACK_PASSENGERS

    @staticmethod
    def estimate_from_distance(distance_km: float) -> int:
        """
        Model kullanılmadığında mantıklı varsayılan: mesafe * 0.12 (min 40, max 350).
        UI'a giden veride model_kullanildi=False olacak (ml_predicted=False).
        """
        if distance_km <= 0:
            return FALLBACK_PASSENGERS
        pax = int(round(distance_km * FALLBACK_RATE))
        return max(PAX_MIN, min(PAX_MAX, pax))
