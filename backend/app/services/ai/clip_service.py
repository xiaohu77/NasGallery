import logging
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image
import io
import threading
import time

logger = logging.getLogger(__name__)

# 模型配置
MODEL_DIR = Path(__file__).parent.parent.parent.parent / "data" / "ai_models" / "chinese-clip"
EMBEDDING_DIM = 512  # CLIP 输出维度
IDLE_TIMEOUT = 30 * 60  # 空闲超时时间（30分钟）


class CLIPService:
    """Chinese-CLIP 模型服务"""
    
    def __init__(self):
        self.image_session = None
        self.text_session = None
        self.tokenizer = None
        self.model_loaded = False
        self.model_version = "clip-v1"
        self.use_single_model = False
        self.current_provider = None  # 当前使用的提供程序
        
        # 空闲超时相关
        self.last_used_time = None
        self._unload_timer = None
        self._lock = threading.Lock()
    
    def get_available_providers(self) -> Dict[str, Any]:
        """获取可用的执行提供程序"""
        import onnxruntime as ort
        import subprocess
        
        available = ort.get_available_providers()
        
        providers_info = {
            'available': available,
            'gpu_providers': [],
            'cpu_available': 'CPUExecutionProvider' in available
        }
        
        # 获取实际 GPU 型号
        gpu_name = self._get_gpu_name()
        
        # 检查 GPU 提供程序
        if 'OpenVINOExecutionProvider' in available:
            providers_info['gpu_providers'].append({
                'name': 'OpenVINOExecutionProvider',
                'display_name': gpu_name or 'Intel GPU',
                'description': 'Intel 集成显卡加速 (OpenVINO)'
            })
        
        if 'AzureExecutionProvider' in available:
            providers_info['gpu_providers'].append({
                'name': 'AzureExecutionProvider',
                'display_name': gpu_name or 'Intel GPU',
                'description': 'Intel 集成显卡加速 (Azure)'
            })
        
        if 'CUDAExecutionProvider' in available:
            cuda_name = self._get_cuda_gpu_name()
            providers_info['gpu_providers'].append({
                'name': 'CUDAExecutionProvider',
                'display_name': cuda_name or 'NVIDIA GPU',
                'description': 'NVIDIA 独立显卡加速'
            })
        
        if 'DmlExecutionProvider' in available:
            providers_info['gpu_providers'].append({
                'name': 'DmlExecutionProvider',
                'display_name': 'DirectML GPU',
                'description': 'Windows GPU 加速'
            })
        
        return providers_info
    
    def _get_gpu_name(self) -> Optional[str]:
        """获取 Intel GPU 型号"""
        try:
            import subprocess
            # Linux: 通过 lspci 获取
            result = subprocess.run(
                ['lspci'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'VGA' in line and 'Intel' in line:
                        # 提取 GPU 名称，如 "Intel Corporation Alder Lake-S GT1 [UHD Graphics 730]"
                        if '[' in line and ']' in line:
                            name = line.split('[')[1].split(']')[0]
                            return f"Intel {name}"
                        return "Intel GPU"
        except Exception:
            pass
        return None
    
    def _get_cuda_gpu_name(self) -> Optional[str]:
        """获取 NVIDIA GPU 型号"""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def load_model(self, use_gpu: bool = True, provider_name: Optional[str] = None) -> bool:
        """
        加载 CLIP 模型
        
        Args:
            use_gpu: 是否使用 GPU
            provider_name: 指定使用的提供程序名称，None 则自动选择
            
        Returns:
            是否加载成功
        """
        try:
            import onnxruntime as ort
            
            # 检查模型文件
            # 支持两种模式：分离的 image/text 模型 或 单个合并模型
            image_model_path = MODEL_DIR / "image_model.onnx"
            text_model_path = MODEL_DIR / "text_model.onnx"
            single_model_path = MODEL_DIR / "model.onnx"
            
            use_single_model = False
            
            if image_model_path.exists() and text_model_path.exists():
                # 使用分离的模型
                pass
            elif single_model_path.exists():
                # 使用单个合并模型
                use_single_model = True
                image_model_path = single_model_path
                text_model_path = single_model_path
            else:
                logger.warning(f"模型文件不存在: {MODEL_DIR}")
                logger.info(f"请下载 Chinese-CLIP ONNX 模型到: {MODEL_DIR}")
                return False
            
            # 配置执行提供程序
            providers = []
            if use_gpu and provider_name:
                # 使用指定的提供程序
                providers.append(provider_name)
            elif use_gpu:
                # 自动选择：优先 OpenVINO，其次 CUDA
                available = self.get_available_providers()
                for gpu_provider in available['gpu_providers']:
                    providers.append(gpu_provider['name'])
            
            # 始终添加 CPU 作为回退
            providers.append('CPUExecutionProvider')
            
            # 加载模型
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            if use_single_model:
                # 单文件模式：加载同一个模型用于图片和文本
                self.image_session = ort.InferenceSession(
                    str(image_model_path),
                    sess_options,
                    providers=providers
                )
                # 文本使用同一个模型
                self.text_session = self.image_session
                self.use_single_model = True
                logger.info(f"使用单文件模型模式")
            else:
                # 分离模型模式
                self.image_session = ort.InferenceSession(
                    str(image_model_path),
                    sess_options,
                    providers=providers
                )
                
                self.text_session = ort.InferenceSession(
                    str(text_model_path),
                    sess_options,
                    providers=providers
                )
                self.use_single_model = False
            
            # 加载 tokenizer
            self._load_tokenizer()
            
            self.model_loaded = True
            self.current_provider = self.image_session.get_providers()[0]
            logger.info(f"CLIP 模型加载成功，使用: {self.image_session.get_providers()}")
            
            # 更新使用时间并启动空闲超时检测
            self._update_last_used()
            
            return True
            
        except ImportError as e:
            logger.error(f"缺少依赖: {e}")
            return False
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def _update_last_used(self):
        """更新最后使用时间并重置卸载定时器"""
        with self._lock:
            self.last_used_time = time.time()
            self._reset_unload_timer()
    
    def _reset_unload_timer(self):
        """重置卸载定时器"""
        # 取消现有定时器
        if self._unload_timer is not None:
            self._unload_timer.cancel()
        
        # 启动新定时器
        self._unload_timer = threading.Timer(IDLE_TIMEOUT, self._check_and_unload)
        self._unload_timer.daemon = True
        self._unload_timer.start()
    
    def _check_and_unload(self):
        """检查是否应该卸载模型"""
        with self._lock:
            if self.last_used_time is None:
                return
            
            idle_time = time.time() - self.last_used_time
            if idle_time >= IDLE_TIMEOUT and self.model_loaded:
                logger.info(f"模型空闲超过 {IDLE_TIMEOUT // 60} 分钟，自动卸载")
                self.unload_model()
    
    def _load_tokenizer(self):
        """加载 tokenizer"""
        try:
            from transformers import BertTokenizer
            tokenizer_path = MODEL_DIR / "tokenizer"
            if tokenizer_path.exists():
                self.tokenizer = BertTokenizer.from_pretrained(str(tokenizer_path))
            else:
                logger.warning("Tokenizer 不存在，将使用简单分词")
                self.tokenizer = None
        except Exception as e:
            logger.warning(f"加载 tokenizer 失败: {e}")
            self.tokenizer = None
    
    def encode_image(self, image_data: bytes) -> Optional[np.ndarray]:
        """
        编码图片为向量
        
        Args:
            image_data: 图片二进制数据
            
        Returns:
            512维向量，失败返回 None
        """
        if not self.model_loaded:
            logger.error("模型未加载")
            return None
        
        # 更新使用时间
        self._update_last_used()
        
        try:
            # 预处理图片
            img = Image.open(io.BytesIO(image_data)).convert('RGB')
            img = img.resize((224, 224), Image.Resampling.LANCZOS)
            
            # 转换为 numpy 数组
            img_array = np.array(img, dtype=np.float32)
            img_array = img_array / 255.0  # 归一化
            
            # ImageNet 标准化
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img_array = (img_array - mean) / std
            
            # 转换为 NCHW 格式
            img_array = np.transpose(img_array, (2, 0, 1))
            img_array = np.expand_dims(img_array, axis=0).astype(np.float32)
            
            # 模型需要所有输入，使用 dummy 文本输入
            dummy_ids = np.zeros((1, 64), dtype=np.int64)
            dummy_mask = np.zeros((1, 64), dtype=np.int64)
            
            # 推理
            output = self.image_session.run(
                ['image_embeds'],
                {
                    'pixel_values': img_array,
                    'input_ids': dummy_ids,
                    'attention_mask': dummy_mask
                }
            )
            
            # 获取嵌入向量并归一化
            embedding = output[0].flatten()
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"编码图片失败: {e}")
            return None
    
    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        编码文本为向量
        
        Args:
            text: 输入文本
            
        Returns:
            512维向量，失败返回 None
        """
        if not self.model_loaded:
            logger.error("模型未加载")
            return None
        
        # 更新使用时间
        self._update_last_used()
        
        try:
            # Tokenize
            if self.tokenizer:
                tokens = self.tokenizer(
                    text,
                    padding='max_length',
                    truncation=True,
                    max_length=64,
                    return_tensors='np'
                )
                input_ids = tokens['input_ids'].astype(np.int64)
                attention_mask = tokens['attention_mask'].astype(np.int64)
            else:
                # 简单的字符级分词（备用方案）
                input_ids = self._simple_tokenize(text)
                attention_mask = np.ones_like(input_ids)
            
            # 模型需要所有输入，使用 dummy 图片输入
            dummy_img = np.zeros((1, 3, 224, 224), dtype=np.float32)
            
            # 推理
            output = self.text_session.run(
                ['text_embeds'],
                {
                    'input_ids': input_ids,
                    'attention_mask': attention_mask,
                    'pixel_values': dummy_img
                }
            )
            
            # 获取嵌入向量并归一化
            embedding = output[0].flatten()
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"编码文本失败: {e}")
            return None
    
    def _simple_tokenize(self, text: str, max_length: int = 64) -> np.ndarray:
        """简单的字符级分词"""
        # 将字符转换为 Unicode 码点
        tokens = [ord(c) for c in text[:max_length-2]]
        # 添加 [CLS] 和 [SEP]
        tokens = [101] + tokens + [102]
        # Padding
        tokens = tokens + [0] * (max_length - len(tokens))
        return np.array([tokens], dtype=np.int64)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """计算两个向量的余弦相似度"""
        return float(np.dot(embedding1, embedding2))
    
    def is_available(self) -> bool:
        """检查模型是否可用（已加载）"""
        return self.model_loaded
    
    def has_model_files(self) -> bool:
        """检查模型文件是否存在"""
        image_model_path = MODEL_DIR / "image_model.onnx"
        text_model_path = MODEL_DIR / "text_model.onnx"
        single_model_path = MODEL_DIR / "model.onnx"
        
        has_separate = image_model_path.exists() and text_model_path.exists()
        has_single = single_model_path.exists()
        
        return has_separate or has_single
    
    def unload_model(self) -> bool:
        """卸载模型释放内存"""
        try:
            # 取消定时器
            with self._lock:
                if self._unload_timer is not None:
                    self._unload_timer.cancel()
                    self._unload_timer = None
                self.last_used_time = None
            
            self.image_session = None
            self.text_session = None
            self.tokenizer = None
            self.model_loaded = False
            self.current_provider = None
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            logger.info("CLIP 模型已卸载，内存已释放")
            return True
        except Exception as e:
            logger.error(f"卸载模型失败: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "loaded": self.model_loaded,
            "version": self.model_version,
            "embedding_dim": EMBEDDING_DIM,
            "model_dir": str(MODEL_DIR),
            "providers": self.image_session.get_providers() if self.model_loaded else [],
            "current_provider": self.current_provider,
            "available_providers": self.get_available_providers()
        }


# 全局实例
clip_service = CLIPService()
