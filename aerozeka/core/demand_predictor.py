# -*- coding: utf-8 -*-
"""
Yolcu talebi tahmini: ml/demand_model.pkl ile tahmin.
Model yoksa güvenli yedek (fallback) değer kullanılır.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

# Proje ana dizini: aerozeka/core -> aerozeka -> proje kökü
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = _PROJECT_ROOT / "ml" / "demand_model.pkl"
FALLBACK_PASSENGERS = 150  # Model yoksa kullanılacak sabit


class DemandPredictor:
    """
    Eğitilmiş RandomForest modeli ile rota/tarih bazlı yolcu tahmini.
    Model dosyası yoksa predict None döner ve terminale uyarı yazılır.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self._path = Path(model_path) if model_path else MODEL_PATH
        self._model = None
        self._loaded = False

    def load_model(self) -> bool:
        """
        demand_model.pkl dosyasını belleğe yükler.
        Başarılıysa True, dosya yoksa veya hata varsa False (ve terminale uyarı).
        """
        if self._loaded and self._model is not None:
            return True
        if not self._path.is_file():
            print("Lütfen önce modeli eğitin: python -m ml.train_demand_model veya proje kökünden ml/train_demand_model.py çalıştırın.")
            return False
        try:
            import joblib
            self._model = joblib.load(self._path)
            self._loaded = True
            return True
        except Exception as e:
            print(f"Model yüklenemedi: {e}. Yedek yolcu sayısı kullanılacak.")
            return False

    def predict(
        self,
        distance_km: float,
        date: Optional[datetime] = None,
    ) -> Optional[int]:
        """
        Mesafe ve tarih ile tahmini yolcu sayısı döndürür.
        date yoksa bugün kullanılır. Model yoksa None (fallback kullanılacak).
        """
        if not self.load_model() or self._model is None:
            return None
        when = date or datetime.now()
        ay = when.month
        haftanin_gunu = when.weekday()  # 0=Pazartesi, 6=Pazar
        tatil_mi = 1 if haftanin_gunu >= 5 else 0  # Hafta sonu = tatil

        try:
            import numpy as np
            X = np.array([[distance_km, ay, haftanin_gunu, tatil_mi]])
            pred = self._model.predict(X)
            return int(round(float(pred[0])))
        except Exception:
            return None

    @staticmethod
    def fallback_passengers() -> int:
        """Model kullanılamadığında döndürülecek güvenli değer."""
        return FALLBACK_PASSENGERS
