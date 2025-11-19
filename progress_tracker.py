import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class TranslationStatus(Enum):
    """翻译状态枚举"""
    PENDING = "pending"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslationProgress:
    """翻译进度管理器"""
    
    def __init__(self, progress_file: str = ".translation_progress.json"):
        self.progress_file = progress_file
        self.progress_data: Dict[str, dict] = {}
        self.load()
    
    def load(self):
        """从文件加载进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.progress_data = json.load(f)
                print(f"已加载翻译进度: {len(self.progress_data)} 篇文章")
            except Exception as e:
                print(f"加载进度文件失败: {e}")
                self.progress_data = {}
        else:
            print("未找到进度文件，将创建新的进度跟踪")
            self.progress_data = {}
    
    def save(self):
        """保存进度到文件"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存进度文件失败: {e}")
    
    def get_status(self, url: str) -> Optional[str]:
        """获取文章翻译状态"""
        if url in self.progress_data:
            return self.progress_data[url].get('status')
        return None
    
    def set_status(self, url: str, status: TranslationStatus, error: str = None):
        """设置文章翻译状态"""
        if url not in self.progress_data:
            self.progress_data[url] = {}
        
        self.progress_data[url]['status'] = status.value
        self.progress_data[url]['updated_at'] = datetime.now().isoformat()
        
        if error:
            self.progress_data[url]['error'] = error
        elif 'error' in self.progress_data[url]:
            del self.progress_data[url]['error']
        
        self.save()
    
    def is_completed(self, url: str) -> bool:
        """检查文章是否已完成翻译"""
        return self.get_status(url) == TranslationStatus.COMPLETED.value
    
    def is_failed(self, url: str) -> bool:
        """检查文章翻译是否失败"""
        return self.get_status(url) == TranslationStatus.FAILED.value
    
    def get_failed_articles(self) -> List[str]:
        """获取所有翻译失败的文章URL"""
        return [
            url for url, data in self.progress_data.items()
            if data.get('status') == TranslationStatus.FAILED.value
        ]
    
    def reset_failed(self):
        """重置所有失败的文章状态为待处理"""
        for url, data in self.progress_data.items():
            if data.get('status') == TranslationStatus.FAILED.value:
                data['status'] = TranslationStatus.PENDING.value
                data['updated_at'] = datetime.now().isoformat()
                if 'error' in data:
                    del data['error']
        self.save()
    
    def get_statistics(self) -> dict:
        """获取翻译统计信息"""
        stats = {
            'total': len(self.progress_data),
            'completed': 0,
            'failed': 0,
            'translating': 0,
            'pending': 0
        }
        
        for data in self.progress_data.values():
            status = data.get('status', 'pending')
            if status == TranslationStatus.COMPLETED.value:
                stats['completed'] += 1
            elif status == TranslationStatus.FAILED.value:
                stats['failed'] += 1
            elif status == TranslationStatus.TRANSLATING.value:
                stats['translating'] += 1
            else:
                stats['pending'] += 1
        
        return stats
