# -*- coding: utf-8 -*-
"""
成本跟踪模块
跟踪LLM API调用成本、Token使用量和响应时间
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CostRecord:
    """成本记录数据类"""
    timestamp: datetime
    model: str
    provider: str  # ollama, deepseek, moonshot等
    operation: str  # chat, reasoning, embedding等
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    session_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ProviderPricing:
    """提供商定价信息"""
    name: str
    models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def get_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        if model not in self.models:
            return 0.0
        
        pricing = self.models[model]
        input_cost = input_tokens * pricing.get("input_per_1k", 0.0) / 1000
        output_cost = output_tokens * pricing.get("output_per_1k", 0.0) / 1000
        
        return input_cost + output_cost


class CostTracker:
    """成本跟踪器"""
    
    def __init__(self, save_path: str = "./data/cost_tracking.json"):
        """初始化成本跟踪器"""
        self.save_path = Path(save_path)
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.records: List[CostRecord] = []
        self.session_stats: Dict[str, Dict[str, Any]] = {}
        self.total_stats: Dict[str, Any] = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_requests": 0,
            "total_errors": 0
        }
        
        self._lock = threading.Lock()
        self._load_pricing()
        self._load_existing_data()
    
    def _load_pricing(self):
        """加载定价信息"""
        self.pricing = {
            "deepseek": ProviderPricing(
                name="deepseek",
                models={
                    "deepseek-chat": {
                        "input_per_1k": 0.14,   # $0.14 per 1K input tokens
                        "output_per_1k": 0.28   # $0.28 per 1K output tokens
                    },
                    "deepseek-reasoner": {
                        "input_per_1k": 0.55,   # $0.55 per 1K input tokens
                        "output_per_1k": 2.19   # $2.19 per 1K output tokens
                    },
                    "deepseek-coder": {
                        "input_per_1k": 0.14,
                        "output_per_1k": 0.28
                    }
                }
            ),
            "moonshot": ProviderPricing(
                name="moonshot",
                models={
                    "moonshot-v1-8k": {
                        "input_per_1k": 0.01,
                        "output_per_1k": 0.01
                    },
                    "moonshot-v1-32k": {
                        "input_per_1k": 0.024,
                        "output_per_1k": 0.024
                    },
                    "moonshot-v1-128k": {
                        "input_per_1k": 0.06,
                        "output_per_1k": 0.06
                    }
                }
            ),
            "ollama": ProviderPricing(
                name="ollama",
                models={
                    # 本地模型成本为0
                    "gemma3:4b": {"input_per_1k": 0.0, "output_per_1k": 0.0},
                    "qwen3:32b": {"input_per_1k": 0.0, "output_per_1k": 0.0},
                    "qwen2.5-vl:7b": {"input_per_1k": 0.0, "output_per_1k": 0.0}
                }
            )
        }
    
    def _load_existing_data(self):
        """加载已存在的数据"""
        try:
            if self.save_path.exists():
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 重建记录
                    for record_data in data.get("records", []):
                        record = CostRecord(
                            timestamp=datetime.fromisoformat(record_data["timestamp"]),
                            model=record_data["model"],
                            provider=record_data["provider"],
                            operation=record_data["operation"],
                            input_tokens=record_data["input_tokens"],
                            output_tokens=record_data["output_tokens"],
                            total_tokens=record_data["total_tokens"],
                            cost_usd=record_data.get("cost_usd", 0.0),
                            latency_ms=record_data.get("latency_ms", 0.0),
                            session_id=record_data.get("session_id"),
                            success=record_data.get("success", True),
                            error_message=record_data.get("error_message")
                        )
                        self.records.append(record)
                    
                    self.total_stats = data.get("total_stats", self.total_stats)
                    
                    logger.info(f"Loaded {len(self.records)} cost records from {self.save_path}")
        except Exception as e:
            logger.warning(f"Failed to load existing cost data: {e}")
    
    def record_usage(
        self, 
        model: str,
        provider: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float = 0.0,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> CostRecord:
        """记录使用情况"""
        
        total_tokens = input_tokens + output_tokens
        cost_usd = 0.0
        
        # 计算成本
        if provider in self.pricing:
            cost_usd = self.pricing[provider].get_cost(model, input_tokens, output_tokens)
        
        record = CostRecord(
            timestamp=datetime.now(),
            model=model,
            provider=provider,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            session_id=session_id,
            success=success,
            error_message=error_message
        )
        
        with self._lock:
            self.records.append(record)
            
            # 更新总统计
            self.total_stats["total_cost"] += cost_usd
            self.total_stats["total_tokens"] += total_tokens
            self.total_stats["total_requests"] += 1
            if not success:
                self.total_stats["total_errors"] += 1
            
            # 更新会话统计
            if session_id:
                if session_id not in self.session_stats:
                    self.session_stats[session_id] = {
                        "cost": 0.0, "tokens": 0, "requests": 0, "errors": 0
                    }
                
                session_stat = self.session_stats[session_id]
                session_stat["cost"] += cost_usd
                session_stat["tokens"] += total_tokens
                session_stat["requests"] += 1
                if not success:
                    session_stat["errors"] += 1
        
        logger.debug(f"Recorded usage: {provider}/{model} - ${cost_usd:.4f}")
        return record
    
    def get_stats(self, session_id: Optional[str] = None, 
                  hours: Optional[int] = None) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            if session_id:
                return self.session_stats.get(session_id, {})
            
            # 过滤时间范围
            records = self.records
            if hours:
                cutoff = datetime.now() - timedelta(hours=hours)
                records = [r for r in records if r.timestamp >= cutoff]
            
            total_cost = sum(r.cost_usd for r in records)
            total_tokens = sum(r.total_tokens for r in records)
            success_count = sum(1 for r in records if r.success)
            error_count = len(records) - success_count
            
            # 按提供商分组
            by_provider = {}
            for record in records:
                if record.provider not in by_provider:
                    by_provider[record.provider] = {
                        "cost": 0.0, "tokens": 0, "requests": 0
                    }
                by_provider[record.provider]["cost"] += record.cost_usd
                by_provider[record.provider]["tokens"] += record.total_tokens
                by_provider[record.provider]["requests"] += 1
            
            # 平均延迟
            avg_latency = 0.0
            if records:
                avg_latency = sum(r.latency_ms for r in records) / len(records)
            
            return {
                "period_hours": hours,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "total_requests": len(records),
                "success_requests": success_count,
                "error_requests": error_count,
                "success_rate": success_count / len(records) if records else 0.0,
                "avg_latency_ms": avg_latency,
                "by_provider": by_provider,
                "cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0.0
            }
    
    def get_cost_breakdown(self, hours: int = 24) -> Dict[str, Any]:
        """获取成本明细"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_records = [r for r in self.records if r.timestamp >= cutoff]
        
        breakdown = {
            "total_cost": sum(r.cost_usd for r in recent_records),
            "by_model": {},
            "by_operation": {},
            "hourly_cost": []
        }
        
        # 按模型分组
        for record in recent_records:
            model_key = f"{record.provider}/{record.model}"
            if model_key not in breakdown["by_model"]:
                breakdown["by_model"][model_key] = 0.0
            breakdown["by_model"][model_key] += record.cost_usd
        
        # 按操作分组
        for record in recent_records:
            if record.operation not in breakdown["by_operation"]:
                breakdown["by_operation"][record.operation] = 0.0
            breakdown["by_operation"][record.operation] += record.cost_usd
        
        return breakdown
    
    def save_data(self) -> bool:
        """保存数据到文件"""
        try:
            with self._lock:
                data = {
                    "total_stats": self.total_stats,
                    "session_stats": self.session_stats,
                    "records": [
                        {
                            "timestamp": r.timestamp.isoformat(),
                            "model": r.model,
                            "provider": r.provider,
                            "operation": r.operation,
                            "input_tokens": r.input_tokens,
                            "output_tokens": r.output_tokens,
                            "total_tokens": r.total_tokens,
                            "cost_usd": r.cost_usd,
                            "latency_ms": r.latency_ms,
                            "session_id": r.session_id,
                            "success": r.success,
                            "error_message": r.error_message
                        }
                        for r in self.records
                    ]
                }
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved cost tracking data to {self.save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cost tracking data: {e}")
            return False
    
    def cleanup_old_records(self, days: int = 30):
        """清理旧记录"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self._lock:
            old_count = len(self.records)
            self.records = [r for r in self.records if r.timestamp >= cutoff]
            removed_count = old_count - len(self.records)
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old cost records")


# 全局成本跟踪器实例
cost_tracker = CostTracker()


def track_cost(
    model: str,
    provider: str,
    operation: str = "chat",
    session_id: Optional[str] = None
):
    """成本跟踪装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            input_tokens = 0
            output_tokens = 0
            
            try:
                result = func(*args, **kwargs)
                
                # 尝试从结果中提取token信息
                if hasattr(result, 'usage'):
                    input_tokens = getattr(result.usage, 'prompt_tokens', 0)
                    output_tokens = getattr(result.usage, 'completion_tokens', 0)
                elif isinstance(result, dict):
                    usage = result.get('usage', {})
                    input_tokens = usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0)
                
                return result
                
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            
            finally:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                cost_tracker.record_usage(
                    model=model,
                    provider=provider,
                    operation=operation,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    session_id=session_id,
                    success=success,
                    error_message=error_message
                )
        
        return wrapper
    return decorator
