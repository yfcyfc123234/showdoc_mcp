"""
验证码识别工具。
使用 PaddleOCR（免费开源，无需注册，纯 Python 库）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import cv2  # type: ignore
import numpy as np  # type: ignore

from .exceptions import ShowDocCaptchaError

# 延迟导入 PaddleOCR（首次使用时会自动下载模型）
_paddleocr = None

# CaptchaSolver 单例实例（避免重复初始化 PaddleOCR）
_captcha_solver_instance = None


def _get_paddleocr():
    """获取 PaddleOCR 实例（延迟加载，单例模式）"""
    global _paddleocr
    if _paddleocr is None:
        # 导入 PaddleOCR，使用默认路径
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ShowDocCaptchaError(
                "PaddleOCR 未安装。请运行: pip install paddlepaddle paddleocr"
            )
        
        import warnings
        # 直接创建实例，使用默认路径（用户主目录下的 .paddlex）
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            _paddleocr = PaddleOCR(use_angle_cls=True, lang='en')
    
    return _paddleocr


@dataclass
class CaptchaSolveResult:
    text: str
    confidence: float


def get_captcha_solver(
        whitelist: str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        min_confidence: float = 0.5,
) -> 'CaptchaSolver':
    """获取 CaptchaSolver 单例实例"""
    global _captcha_solver_instance
    if _captcha_solver_instance is None:
        _captcha_solver_instance = CaptchaSolver(whitelist, min_confidence)
    return _captcha_solver_instance


class CaptchaSolver:
    """
    基于 OpenCV + PaddleOCR 的验证码识别器。
    使用 PaddleOCR（免费开源，无需注册，纯 Python 库）。
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

        # 预处理图像
        processed = self._preprocess(img)

        # 使用 PaddleOCR 识别
        # 直接调用，不捕获异常，让真实错误信息透传
        ocr = _get_paddleocr()
        # 新版本 PaddleOCR 可能不支持 cls 参数，先尝试不带参数
        try:
            result = ocr.ocr(processed, cls=True)
        except TypeError:
            # 如果不支持 cls 参数，使用默认参数
            result = ocr.ocr(processed)

        # 解析识别结果
        text_parts = []
        confidences = []

        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if text_info:
                        text = text_info[0]  # 识别的文本
                        confidence = text_info[1]  # 置信度
                        # 只保留白名单中的字符
                        filtered_text = "".join(c for c in text if c in self.whitelist)
                        if filtered_text:
                            text_parts.append(filtered_text)
                            confidences.append(confidence)

        if not text_parts:
            raise ShowDocCaptchaError("验证码识别为空")

        # 合并所有识别到的文本
        text = "".join(text_parts)
        cleaned = re.sub(r"[^0-9a-zA-Z]", "", text).strip()

        # 计算平均置信度
        confidence = sum(confidences) / len(confidences) if confidences else 0.0

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
