"""
验证码识别工具 - 使用 ddddocr
ddddocr 是一个通用的验证码识别 OCR 库，基于深度学习训练
适合：各种类型的验证码（数字、字母、混合等）

项目地址: https://github.com/sml2h3/ddddocr
"""
from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

import cv2  # type: ignore
import numpy as np  # type: ignore

from .exceptions import ShowDocCaptchaError

# 延迟导入 ddddocr
_ddddocr = None
_enable_debug_log = False


def _get_ddddocr():
    """获取 ddddocr 模块"""
    global _ddddocr
    if _ddddocr is None:
        try:
            import ddddocr
            _ddddocr = ddddocr
        except ImportError:
            raise ShowDocCaptchaError(
                "ddddocr 未安装。请运行: pip install ddddocr"
            )
    return _ddddocr


@dataclass
class CaptchaSolveResult:
    text: str
    confidence: float


def get_captcha_solver(
        whitelist: str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        min_confidence: float = 0.5,
) -> 'SimpleCaptchaSolver':
    """获取 SimpleCaptchaSolver 实例"""
    return SimpleCaptchaSolver(whitelist, min_confidence)


class SimpleCaptchaSolver:
    """
    验证码识别器 - 使用 ddddocr
    ddddocr 是基于深度学习的通用验证码识别库，识别准确率高
    
    优点：
    - 识别准确率高
    - 支持多种验证码类型（数字、字母、混合）
    - 无需额外安装 OCR 程序
    - 纯 Python 实现，易于部署
    """

    def __init__(
            self,
            whitelist: str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
            min_confidence: float = 0.5,
            save_variants: bool = True,
            show_ad: bool = False,
    ) -> None:
        """
        初始化验证码识别器
        
        Args:
            whitelist: 允许的字符集合，用于限制识别范围
            min_confidence: 最小置信度阈值（保留接口兼容性）
            save_variants: 是否保存预处理变体图片用于调试
            show_ad: 是否显示 ddddocr 的广告信息（默认 False）
        """
        self.whitelist = whitelist
        self.min_confidence = min_confidence
        self.save_variants = save_variants
        
        # 初始化 ddddocr
        ddddocr_module = _get_ddddocr()
        self.ocr = ddddocr_module.DdddOcr(show_ad=show_ad)
        
        # 如果提供了 whitelist，尝试设置字符范围限制（如果方法存在）
        if whitelist and hasattr(self.ocr, 'set_ranges'):
            try:
                self.ocr.set_ranges(whitelist)
            except Exception:
                # set_ranges 可能在某些版本中不可用，忽略错误
                pass
        
        # 清理旧的调试目录（每次运行都清空）
        self._clean_debug_directory()

    def _clean_debug_directory(self) -> None:
        """清理调试目录，删除所有旧文件（每次运行都清空）"""
        # 获取调试目录路径（支持环境变量自定义）
        debug_dir = Path(os.environ.get("SHOWDOC_CAPTCHA_DEBUG_DIR", "captcha_debug"))
        
        if debug_dir.exists() and debug_dir.is_dir():
            try:
                # 删除整个目录及其所有内容
                shutil.rmtree(debug_dir)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 已清理旧的验证码调试目录: {debug_dir}")
            except Exception as e:
                # 如果删除失败，静默处理（可能是文件被占用等）
                pass

    def solve(self, image_bytes: bytes) -> CaptchaSolveResult:
        """
        对验证码图片进行识别。
        
        Args:
            image_bytes: 验证码图片的字节数据
            
        Returns:
            CaptchaSolveResult: 识别结果，包含文本和置信度
        """
        if not image_bytes:
            raise ShowDocCaptchaError("验证码图片内容为空")

        # 解码图片用于调试保存
        np_img = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if img is None:
            raise ShowDocCaptchaError("无法解码验证码图片")

        errors = []
        debug_session: Optional[Path] = None
        attempt_logs: List[dict] = []
        
        if self.save_variants:
            debug_session = self._start_debug_session(img)
        
        # 使用 ddddocr 直接识别原始图片（效果最好）
        try:
            result = self.ocr.classification(image_bytes)
            if result and isinstance(result, str):
                cleaned = ''.join(c for c in result if c in self.whitelist)
                if cleaned:
                    normalized = self._normalize_result(cleaned)
                    if debug_session is not None:
                        log_entry = {
                            "method": "ddddocr_direct",
                            "raw_text": result,
                            "cleaned": cleaned,
                            "normalized": normalized,
                            "status": "success",
                        }
                        attempt_logs.append(log_entry)
                        self._finalize_debug_session(
                            debug_session,
                            attempt_logs,
                            normalized,
                            success=True,
                        )
                    
                    if _enable_debug_log:
                        print(f"[CaptchaSolver] recognized captcha={normalized} (ddddocr)")
                    
                    return CaptchaSolveResult(text=normalized, confidence=1.0)
                else:
                    errors.append(f"原始识别结果不在允许字符集中: {repr(result)}")
            else:
                errors.append(f"识别结果为空或格式错误: {repr(result)}")
        except Exception as e:
            errors.append(f"ddddocr识别失败: {e}")
            if debug_session is not None:
                attempt_logs.append({
                    "method": "ddddocr_direct",
                    "error": str(e),
                    "status": "error",
                })
        
        # 如果直接识别失败，尝试预处理后的变体
        variants = self._generate_variants(img)
        for idx, (processed, desc) in enumerate(variants, start=1):
            if debug_session is not None:
                self._save_variant_image(debug_session, processed, f"{idx:02d}_{desc}")
            
            try:
                # 将处理后的图片编码为字节
                _, encoded = cv2.imencode('.png', processed)
                variant_bytes = encoded.tobytes()
                
                result = self.ocr.classification(variant_bytes)
                if result and isinstance(result, str):
                    cleaned = ''.join(c for c in result if c in self.whitelist)
                    log_entry = {
                        "variant": desc,
                        "variant_index": idx,
                        "raw_text": result,
                        "cleaned": cleaned,
                    }
                    if cleaned:
                        normalized = self._normalize_result(cleaned)
                        if _enable_debug_log:
                            print(
                                f"[CaptchaSolver] recognized captcha={normalized} "
                                f"(variant={desc})"
                            )
                        if debug_session is not None:
                            log_entry["status"] = "success"
                            log_entry["normalized"] = normalized
                            attempt_logs.append(log_entry)
                            self._finalize_debug_session(
                                debug_session,
                                attempt_logs,
                                normalized,
                                success=True,
                            )
                        return CaptchaSolveResult(text=normalized, confidence=1.0)
                    errors.append(f"{desc}: 识别结果不在允许字符集中, raw={repr(result)}")
                    if debug_session is not None:
                        log_entry["status"] = "empty"
                        attempt_logs.append(log_entry)
                else:
                    errors.append(f"{desc}: 识别结果为空")
                    if debug_session is not None:
                        attempt_logs.append({
                            "variant": desc,
                            "variant_index": idx,
                            "status": "empty",
                        })
            except Exception as e:
                errors.append(f"{desc}: {e}")
                if debug_session is not None:
                    attempt_logs.append({
                        "variant": desc,
                        "variant_index": idx,
                        "error": str(e),
                        "status": "error",
                    })
                continue
        
        if debug_session is not None:
            self._finalize_debug_session(
                debug_session,
                attempt_logs,
                recognized_text=None,
                success=False,
                errors=errors,
            )
        
        raise ShowDocCaptchaError(
            "验证码识别失败。尝试多种预处理仍失败。"
            + (" 详情: " + "; ".join(errors[:5]) if errors else "")
        )

    def _normalize_result(self, text: str) -> str:
        normalized = text.strip().lower()
        return normalized[:4]

    def _generate_variants(self, img: np.ndarray) -> list[tuple[np.ndarray, str]]:
        variants: list[tuple[np.ndarray, str]] = []
        
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        variants.append((gray, "gray"))
        
        denoised = cv2.fastNlMeansDenoising(gray, h=15)
        variants.append((denoised, "denoised"))
        
        equalized = cv2.equalizeHist(denoised)
        variants.append((equalized, "equalized"))
        
        _, binary_otsu = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append((binary_otsu, "binary_otsu"))
        
        binary_inv = cv2.bitwise_not(binary_otsu)
        variants.append((binary_inv, "binary_inv"))
        
        adaptive = cv2.adaptiveThreshold(
            equalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        variants.append((adaptive, "adaptive"))
        variants.append((cv2.bitwise_not(adaptive), "adaptive_inv"))
        
        kernel_small = np.ones((2, 2), np.uint8)
        opened = cv2.morphologyEx(binary_otsu, cv2.MORPH_OPEN, kernel_small, iterations=1)
        variants.append((opened, "open_3x3"))
        
        closed = cv2.morphologyEx(binary_otsu, cv2.MORPH_CLOSE, kernel_small, iterations=1)
        variants.append((closed, "close_3x3"))
        
        kernel_med = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(binary_otsu, kernel_med, iterations=1)
        variants.append((dilated, "dilate_3x3"))
        
        eroded = cv2.erode(binary_otsu, kernel_med, iterations=1)
        variants.append((eroded, "erode_3x3"))
        
        sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpen = cv2.filter2D(equalized, -1, sharpen_kernel)
        variants.append((sharpen, "sharpen"))
        
        scaled_eq = cv2.resize(equalized, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_LINEAR)
        variants.append((scaled_eq, "scaled_equalized"))
        
        scaled_binary = cv2.resize(binary_otsu, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_NEAREST)
        variants.append((scaled_binary, "scaled_binary"))
        
        return variants

    def _start_debug_session(self, original_img: np.ndarray) -> Path:
        root = Path("captcha_debug") / "details"
        root.mkdir(parents=True, exist_ok=True)
        session_dir = root / f"captcha_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        session_dir.mkdir(parents=True, exist_ok=True)
        self._save_variant_image(session_dir, original_img, "original")
        return session_dir

    def _save_variant_image(self, session_dir: Path, image: np.ndarray, name: str) -> None:
        try:
            path = session_dir / f"{name}.png"
            if len(image.shape) == 2:
                cv2.imwrite(str(path), image)
            else:
                cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        except Exception:
            pass

    def _finalize_debug_session(
        self,
        session_dir: Path,
        attempt_logs: List[dict],
        recognized_text: Optional[str],
        success: bool,
        errors: Optional[List[str]] = None,
    ) -> None:
        try:
            meta = {
                "success": success,
                "recognized_text": recognized_text,
                "attempts": attempt_logs,
                "errors": errors or [],
                "timestamp": datetime.now().isoformat(),
            }
            with (session_dir / "metadata.json").open("w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# 为了保持接口兼容性，可以导出相同的类名
# 这样 client.py 不需要修改
CaptchaSolver = SimpleCaptchaSolver

