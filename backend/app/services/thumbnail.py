import io
from pathlib import Path
from typing import List
from PIL import Image

from .archive import ArchiveService

class ThumbnailService:
    """缩略图生成服务：为新入库的CBZ中的图片生成缩略图，按专辑分目录存放在 THUMBNAIL_DIR"""
    def __init__(self, thumbnail_dir: Path):
        self.thumbnail_dir = thumbnail_dir
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        print(f"缩略图服务初始化: {self.thumbnail_dir}")

    def _resize_to_fit_webp(self, image_data: bytes, max_w: int, max_h: int) -> bytes:
        img = Image.open(io.BytesIO(image_data))
        w, h = img.size
        scale = min(max_w / w, max_h / h)
        if scale >= 1:
            # 原图尺寸已在范围内，直接输出 WEBP
            out = io.BytesIO()
            img.save(out, format='WEBP', quality=85)
            return out.getvalue()
        new_w = int(w * scale)
        new_h = int(h * scale)
        # 兼容 Pillow 版本差异：尽量使用 Lanczos 重采样
        if hasattr(Image, 'LANCZOS'):
            resample = Image.LANCZOS
        else:
            resample = Image.BICUBIC
        img = img.resize((new_w, new_h), resample)
        out = io.BytesIO()
        img.save(out, format='WEBP', quality=85)
        return out.getvalue()

    def generate_thumbnails_for_cbz(self, cbz_path: Path, album_id: int, image_list: List[str]):
        """为 CBZ 内指定图片生成缩略图，输出到 THUMBNAIL_DIR

        约定文件名：thumb_{album_id}_{i}_{stem}.webp
        """
        generated = []
        max_w, max_h = 1200, 1800
        # 为每个专辑创建一个单独的子目录
        album_dir = self.thumbnail_dir / str(album_id)
        album_dir.mkdir(parents=True, exist_ok=True)
        for idx, fname in enumerate(image_list, start=1):
            try:
                image_data = ArchiveService.extract_image(cbz_path, fname)
                if not image_data:
                    continue
                thumb_bytes = self._resize_to_fit_webp(image_data, max_w, max_h)
                stem = Path(fname).stem
                out_name = f"thumb_{album_id}_{idx}_{stem}.webp"
                out_path = album_dir / out_name
                with open(out_path, 'wb') as f:
                    f.write(thumb_bytes)
                generated.append(out_path)
            except Exception as e:
                print(f"缩略图生成失败 {fname}: {e}")
        return generated
