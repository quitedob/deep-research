# -*- coding: utf-8 -*-
"""
Real-time Monitoring API Endpoints for Deep Research Platform
Handles system monitoring, performance tracking, and real-time updates
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
import logging
import psutil
import time

from ..core.database import get_db
from ..core.security import get_current_user

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

logger = logging.getLogger(__name__)

# Connected WebSocket clients
_connected_clients = set()

# Monitoring data cache
_monitoring_cache = {
    "system_health": {},
    "agent_activities": [],
    "performance_metrics": {},
    "alerts": [],
    "last_update": None
}

def get_system_health():
    """Get current system health metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        # Network I/O
        network = psutil.net_io_counters()

        # Process count
        process_count = len(psutil.pids())

        return {
            "cpu": round(cpu_percent, 1),
            "memory": round(memory_percent, 1),
            "disk": round(disk_percent, 1),
            "memory_available": round(memory.available / (1024**3), 2),  # GB
            "memory_total": round(memory.total / (1024**3), 2),  # GB
            "disk_free": round(disk.free / (1024**3), 2),  # GB
            "disk_total": round(disk.total / (1024**3), 2),  # GB
            "network_bytes_sent": network.bytes_sent,
            "network_bytes_recv": network.bytes_recv,
            "process_count": process_count,
            "uptime": time.time() - psutil.boot_time()
        }
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return {
            "cpu": 0,
            "memory": 0,
            "disk": 0,
            "error": str(e)
        }

def get_performance_metrics():
    """Get performance metrics"""
    try:
        # Mock performance metrics (in production, these would be real measurements)
        return {
            "response_time": 150 + (hash(str(time.time())) % 100),  # 150-250ms
            "request_rate": 45 + (hash(str(time.time())) % 20),  # 45-65 req/min
            "error_rate": round((hash(str(time.time())) % 5) / 100, 2),  # 0-5%
            "throughput": 1200 + (hash(str(time.time())) % 300),  # 1200-1500 ops/min
            "concurrent_users": 15 + (hash(str(time.time())) % 10),  # 15-25 users
            "cache_hit_rate": 85 + (hash(str(time.time())) % 10),  # 85-95%
            "database_connections": 8 + (hash(str(time.time())) % 4),  # 8-12 connections
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return {
            "response_time": 0,
            "error_rate": 0,
            "error": str(e)
        }

def generate_agent_activities():
    """Generate mock agent activities"""
    agent_types = ["research_agent", "evidence_agent", "synthesis_agent"]
    activities = []

    for agent_type in agent_types:
        # Generate 1-3 activities per agent type
        for i in range(hash(str(time.time())) % 3 + 1):
            activities.append({
                "id": f"activity_{agent_type}_{int(time.time() * 1000)}_{i}",
                "agentId": f"{agent_type}_{hash(str(time.time())) % 3 + 1}",
                "agentName": f"{agent_type.replace('_', ' ').title()} {hash(str(time.time())) % 3 + 1}",
                "type": "task_execution" if i == 0 else "evidence_collection",
                "description": f"Processing research task #{i+1}",
                "status": "running" if i % 3 != 0 else "completed",
                "progress": 25 + (i * 25) + (hash(str(time.time())) % 20),
                "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                "details": f"Agent is processing research data with high accuracy"
            })

    return activities

def check_system_alerts():
    """Check for system alerts"""
    alerts = []
    system_health = get_system_health()

    # CPU alert
    if system_health.get("cpu", 0) > 80:
        alerts.append({
            "id": f"alert_cpu_{int(time.time())}",
            "level": "warning" if system_health["cpu"] < 90 else "error",
            "title": "High CPU Usage",
            "message": f"CPU usage is at {system_health['cpu']}%",
            "timestamp": datetime.now().isoformat()
        })

    # Memory alert
    if system_health.get("memory", 0) > 85:
        alerts.append({
            "id": f"alert_memory_{int(time.time())}",
            "level": "error",
            "title": "High Memory Usage",
            "message": f"Memory usage is at {system_health['memory']}%",
            "timestamp": datetime.now().isoformat()
        })

    # Disk alert
    if system_health.get("disk", 0) > 90:
        alerts.append({
            "id": f"alert_disk_{int(time.time())}",
            "level": "error",
            "title": "Low Disk Space",
            "message": f"Disk usage is at {system_health['disk']}%",
            "timestamp": datetime.now().isoformat()
        })

    return alerts

async def update_monitoring_data():
    """Update monitoring data cache"""
    global _monitoring_cache

    try:
        _monitoring_cache["system_health"] = get_system_health()
        _monitoring_cache["performance_metrics"] = get_performance_metrics()
        _monitoring_cache["agent_activities"] = generate_agent_activities()
        _monitoring_cache["alerts"] = check_system_alerts()
        _monitoring_cache["last_update"] = datetime.now().isoformat()

        # Limit activities to last 50
        if len(_monitoring_cache["agent_activities"]) > 50:
            _monitoring_cache["agent_activities"] = _monitoring_cache["agent_activities"][-50:]

        # Limit alerts to last 20
        if len(_monitoring_cache["alerts"]) > 20:
            _monitoring_cache["alerts"] = _monitoring_cache["alerts"][-20:]

    except Exception as e:
        logger.error(f"Failed to update monitoring data: {e}")

async def broadcast_to_clients(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    if _connected_clients:
        message_str = json.dumps(message)
        disconnected_clients = set()

        for client in _connected_clients:
            try:
                await client.send_text(message_str)
            except:
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            _connected_clients.discard(client)

# Monitoring Endpoints

@router.get("/system-health")
async def get_system_health_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current system health status"""
    try:
        await update_monitoring_data()

        return {
            "success": True,
            "health": _monitoring_cache["system_health"],
            "timestamp": _monitoring_cache["last_update"],
            "message": "System health retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")

@router.get("/performance")
async def get_performance_metrics_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics"""
    try:
        await update_monitoring_data()

        return {
            "success": True,
            "metrics": _monitoring_cache["performance_metrics"],
            "timestamp": _monitoring_cache["last_update"],
            "message": "Performance metrics retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/activities")
async def get_agent_activities(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get agent activities"""
    try:
        await update_monitoring_data()

        activities = _monitoring_cache["agent_activities"]

        # Filter by agent type
        if agent_type:
            activities = [a for a in activities if agent_type in a.get("agentName", "").lower()]

        # Filter by status
        if status:
            activities = [a for a in activities if a.get("status") == status]

        # Apply limit
        if limit > 0:
            activities = activities[:limit]

        return {
            "success": True,
            "activities": activities,
            "count": len(activities),
            "timestamp": _monitoring_cache["last_update"],
            "message": "Agent activities retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent activities: {str(e)}")

@router.get("/alerts")
async def get_system_alerts(
    level: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system alerts"""
    try:
        await update_monitoring_data()

        alerts = _monitoring_cache["alerts"]

        # Filter by level
        if level:
            alerts = [a for a in alerts if a.get("level") == level]

        # Apply limit
        if limit > 0:
            alerts = alerts[:limit]

        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": _monitoring_cache["last_update"],
            "message": "System alerts retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system alerts: {str(e)}")

@router.get("/overview")
async def get_monitoring_overview(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive monitoring overview"""
    try:
        await update_monitoring_data()

        overview = {
            "system_health": _monitoring_cache["system_health"],
            "performance_metrics": _monitoring_cache["performance_metrics"],
            "active_agents": len([a for a in _monitoring_cache["agent_activities"] if a.get("status") == "running"]),
            "recent_activities": _monitoring_cache["agent_activities"][:5],
            "active_alerts": len([a for a in _monitoring_cache["alerts"] if a.get("level") in ["error", "warning"]]),
            "timestamp": _monitoring_cache["last_update"]
        }

        return {
            "success": True,
            "overview": overview,
            "message": "Monitoring overview retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring overview: {str(e)}")

@router.get("/logs")
async def get_monitoring_logs(
    level: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monitoring logs"""
    try:
        # Mock log generation (in production, this would retrieve from a log store)
        log_levels = ["debug", "info", "warning", "error"]
        log_sources = ["monitoring", "orchestrator", "agents", "api"]

        logs = []
        for i in range(min(limit, 50)):
            log_level = level or log_levels[hash(str(i)) % len(log_levels)]
            log_source = source or log_sources[hash(str(i * 2)) % len(log_sources)]

            logs.append({
                "id": f"log_{int(time.time() * 1000)}_{i}",
                "level": log_level,
                "source": log_source,
                "message": f"System {log_level} message from {log_source} #{i}",
                "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat()
            })

        return {
            "success": True,
            "logs": logs,
            "count": len(logs),
            "message": "Monitoring logs retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring logs: {str(e)}")

@router.post("/refresh")
async def refresh_monitoring_data(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Force refresh monitoring data"""
    try:
        await update_monitoring_data()

        # Broadcast update to all connected clients
        await broadcast_to_clients({
            "type": "monitoring_update",
            "data": {
                "system_health": _monitoring_cache["system_health"],
                "performance_metrics": _monitoring_cache["performance_metrics"],
                "timestamp": _monitoring_cache["last_update"]
            },
            "timestamp": datetime.now().isoformat()
        })

        return {
            "success": True,
            "timestamp": _monitoring_cache["last_update"],
            "message": "Monitoring data refreshed successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh monitoring data: {str(e)}")

@router.get("/export")
async def export_monitoring_data(
    format: str = "json",
    time_range: str = "1h",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export monitoring data"""
    try:
        await update_monitoring_data()

        # Parse time range
        time_delta = timedelta(hours=1)
        if time_range == "24h":
            time_delta = timedelta(hours=24)
        elif time_range == "7d":
            time_delta = timedelta(days=7)
        elif time_range == "30d":
            time_delta = timedelta(days=30)

        export_data = {
            "export_time": datetime.now().isoformat(),
            "time_range": time_range,
            "exported_by": current_user["id"],
            "system_health": _monitoring_cache["system_health"],
            "performance_metrics": _monitoring_cache["performance_metrics"],
            "agent_activities": _monitoring_cache["agent_activities"],
            "alerts": _monitoring_cache["alerts"],
            "last_update": _monitoring_cache["last_update"]
        }

        if format.lower() == "json":
            return {
                "success": True,
                "data": export_data,
                "format": "json",
                "message": "Monitoring data exported successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export monitoring data: {str(e)}")

# WebSocket Endpoint for Real-time Updates

@router.websocket("/ws")
async def monitoring_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates"""
    await websocket.accept()
    _connected_clients.add(websocket)

    try:
        # Send initial data
        await update_monitoring_data()
        await websocket.send_text(json.dumps({
            "type": "initial_data",
            "data": _monitoring_cache,
            "timestamp": datetime.now().isoformat()
        }))

        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific events
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "events": message.get("events", ["system_health", "alerts"]),
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "refresh":
                    # Force refresh on demand
                    await update_monitoring_data()
                    await websocket.send_text(json.dumps({
                        "type": "monitoring_update",
                        "data": _monitoring_cache,
                        "timestamp": datetime.now().isoformat()
                    }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))

    except WebSocketDisconnect:
        _connected_clients.remove(websocket)
        logger.info("Monitoring WebSocket client disconnected")

# Background task for periodic updates
async def start_monitoring_updates():
    """Start background task for periodic monitoring updates"""
    while True:
        try:
            await update_monitoring_data()

            # Broadcast to connected clients
            await broadcast_to_clients({
                "type": "periodic_update",
                "data": {
                    "system_health": _monitoring_cache["system_health"],
                    "performance_metrics": _monitoring_cache["performance_metrics"],
                    "alerts": _monitoring_cache["alerts"][-5:]  # Last 5 alerts
                },
                "timestamp": _monitoring_cache["last_update"]
            })

        except Exception as e:
            logger.error(f"Failed in monitoring update: {e}")

        # Update every 10 seconds
        await asyncio.sleep(10)