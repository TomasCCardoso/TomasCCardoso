#!/usr/bin/env python3
"""
prep_photo.py — prepara uma foto para conversão em ASCII art.

Passos:
  1. Remove o fundo com rembg (isola o sujeito).
  2. Aplica CLAHE (contraste local adaptativo) para dar profundidade
     a uma foto com luz plana.
  3. Compõe sobre fundo branco puro, para que o fundo mapeie para o
     glifo em branco (espaço) da rampa ASCII.

Uso:
    python scripts/prep_photo.py caminho/para/foto.png
Gera:
    assets/source-prepped.png (grayscale, pronta para make_ascii_svg.py)
"""
import sys
from pathlib import Path

import numpy as np
import cv2
from PIL import Image

MODEL_NAME = "u2netp"  # modelo leve (~4.6 MB) — evita OOM em máquinas pequenas
OUT_PATH = Path("assets/source-prepped.png")


def remove_background(img: Image.Image) -> Image.Image:
    from rembg import remove, new_session

    session = new_session(MODEL_NAME)
    return remove(img, session=session)


def apply_clahe(rgb: np.ndarray) -> np.ndarray:
    """CLAHE no canal L de Lab — realça sombras/luzes sem estourar cor."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge((l2, a, b))
    return cv2.cvtColor(lab2, cv2.COLOR_LAB2RGB)


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/prep_photo.py caminho/para/foto.jpg")
        sys.exit(1)

    src_path = Path(sys.argv[1])
    img = Image.open(src_path).convert("RGB")

    print(f"[1/3] A remover o fundo ({MODEL_NAME})...")
    no_bg = remove_background(img)  # RGBA

    print("[2/3] A aplicar CLAHE (contraste local)...")
    rgba = np.array(no_bg)
    rgb, alpha = rgba[:, :, :3], rgba[:, :, 3]
    rgb_enhanced = apply_clahe(rgb)

    print("[3/3] A compor sobre fundo branco...")
    alpha_f = (alpha.astype(np.float32) / 255.0)[:, :, None]
    white = np.full_like(rgb_enhanced, 255)
    composed = (rgb_enhanced.astype(np.float32) * alpha_f +
                white.astype(np.float32) * (1 - alpha_f)).astype(np.uint8)

    gray = cv2.cvtColor(composed, cv2.COLOR_RGB2GRAY)
    out_img = Image.fromarray(gray, mode="L")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_img.save(OUT_PATH)
    print(f"Gravado em {OUT_PATH} ({out_img.size[0]}x{out_img.size[1]})")


if __name__ == "__main__":
    main()
