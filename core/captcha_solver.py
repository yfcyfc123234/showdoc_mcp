"""
验证码识别工具。
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2  # type: ignore
import numpy as np  # type: ignore
import pytesseract  # type: ignore

from .exceptions import ShowDocCaptchaError


@dataclass
class CaptchaSolveResult:
    text: str
    confidence: float


class CaptchaSolver:
    """
    基于 OpenCV + Tesseract 的简单验证码识别器。
    """

    def __init__(
        self,
        whitelist: str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        min_confidence: float = 0.5,
    ) -> None:
        self.whitelist = whitelist
        self.min_confidence = min_confidence

    def solve(self, image_bytes: bytes) -> CaptchaSolveResult:
        """
        对验证码图片进行识别。
        """
        if not image_bytes:
            raise ShowDocCaptchaError("验证码图片内容为空")

        np_img = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if img is None:
            raise ShowDocCaptchaError("无法解码验证码图片")

        processed = self._preprocess(img)
        config = (
            "--psm 8 --oem 3 "
            f"-c tessedit_char_whitelist={self.whitelist}"
        )

        data = pytesseract.image_to_data(
            processed,
            config=config,
            output_type=pytesseract.Output.DICT,
        )

        text = "".join(char for char in data.get("text", []) if char)
        cleaned = re.sub(r"[^0-9a-zA-Z]", "", text).strip()
        confidence = self._calc_confidence(data)

        if not cleaned:
            raise ShowDocCaptchaError("验证码识别为空")

        return CaptchaSolveResult(text=cleaned, confidence=confidence)

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary = cv2.threshold(
            blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        kernel = np.ones((2, 2), np.uint8)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        return opened

    def _calc_confidence(self, data: dict) -> float:
        conf_list = data.get("conf", [])
        values = []
        for conf in conf_list:
            try:
                value = float(conf)
            except (TypeError, ValueError):
                continue
            if value >= 0:
                values.append(value / 100.0)
        if not values:
            return 0.0
        return sum(values) / len(values)

