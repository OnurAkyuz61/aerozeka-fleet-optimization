# -*- coding: utf-8 -*-
"""
Yolcu talebi tahmini modeli eğitim boru hattı.
Sentetik uçuş geçmişi üretir, RandomForestRegressor eğitir, joblib ile kaydeder.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib

# Model kayıt yolu: proje ana dizinindeki ml/ klasörü
_PROJECT_ROOT = Path(__file__).resolve().parent  # ml/
MODEL_PATH = _PROJECT_ROOT / "demand_model.pkl"

# Sentetik veri boyutu
N_SAMPLES = 5000
RANDOM_STATE = 42


def _generate_synthetic_flight_history() -> pd.DataFrame:
    """
    Özellikler: mesafe_km, ay, haftanin_gunu, tatil_mi -> Hedef: gerceklesen_yolcu.
    Mevsimsel ve tatil etkisi ile anlamlı ilişki kurulur.
    """
    np.random.seed(RANDOM_STATE)

    # Mesafe: 200–1500 km arası
    mesafe_km = np.random.uniform(200, 1500, N_SAMPLES)

    # Ay (1–12), haftanın günü (0=Pazartesi – 6=Pazar)
    ay = np.random.randint(1, 13, N_SAMPLES)
    haftanin_gunu = np.random.randint(0, 7, N_SAMPLES)

    # Tatil: hafta sonu (5,6) veya rastgele ek tatil günleri
    tatil_mi = ((haftanin_gunu >= 5) | (np.random.random(N_SAMPLES) < 0.1)).astype(int)

    # Hedef: gerceklesen_yolcu – mesafe ve mevsim/tatil ile ilişkili + gürültü
    base = 50
    mesafe_etkisi = mesafe_km * 0.08
    ay_etkisi = np.where(ay >= 5, np.where(ay <= 9, 25, 0), 0)  # yaz ayları +yolcu
    gun_etkisi = np.where(haftanin_gunu >= 5, -15, 5)
    tatil_etkisi = np.where(tatil_mi == 1, 20, 0)
    gurultu = np.random.normal(0, 15, N_SAMPLES)

    gerceklesen_yolcu = base + mesafe_etkisi + ay_etkisi + gun_etkisi + tatil_etkisi + gurultu
    gerceklesen_yolcu = np.clip(gerceklesen_yolcu, 40, 250).astype(int)

    df = pd.DataFrame({
        "mesafe_km": mesafe_km,
        "ay": ay,
        "haftanin_gunu": haftanin_gunu,
        "tatil_mi": tatil_mi,
        "gerceklesen_yolcu": gerceklesen_yolcu,
    })
    return df


def train_and_save(
    model_path: os.PathLike | str | None = None,
    test_size: float = 0.2,
) -> str:
    """
    Sentetik veriyi üretir, modeli eğitir ve joblib ile kaydeder.
    Dönen: kaydedilen dosya yolu.
    """
    model_path = Path(model_path) if model_path else MODEL_PATH
    model_path = model_path.resolve()

    df = _generate_synthetic_flight_history()
    X = df[["mesafe_km", "ay", "haftanin_gunu", "tatil_mi"]]
    y = df["gerceklesen_yolcu"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE
    )

    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    # Kayıt dizinini oluştur
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    score = model.score(X_test, y_test)
    print(f"Model eğitildi. R² (test): {score:.4f}. Kayıt: {model_path}")
    return str(model_path)


if __name__ == "__main__":
    train_and_save()
