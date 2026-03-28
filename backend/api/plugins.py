# backend/api/plugins.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.plugin_registry import plugin_registry

router = APIRouter()

class InstallPluginRequest(BaseModel):
    plugin_id: str
    config: dict

class EmitHookRequest(BaseModel):
    hook_name: str
    data: dict

@router.get("/")
def list_all_plugins(category: Optional[str] = None):
    plugins = plugin_registry.list_plugins(category)
    return {
        "plugins": [
            {
                "id": p.id,
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "category": p.category,
                "is_active": p.is_active,
                "config_schema": p.config_schema
            }
            for p in plugins
        ],
        "total": len(plugins),
        "active": sum(1 for p in plugins if p.is_active)
    }

@router.post("/install")
def install_plugin(data: InstallPluginRequest):
    result = plugin_registry.install_plugin(data.plugin_id, data.config)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    return result

@router.delete("/{plugin_id}")
def uninstall_plugin(plugin_id: str):
    return plugin_registry.uninstall_plugin(plugin_id)

@router.get("/active")
def get_active_plugins():
    all_plugins = plugin_registry.list_plugins()
    return {"active_plugins": [p.id for p in all_plugins if p.is_active]}

@router.post("/emit")
def emit_hook(data: EmitHookRequest):
    results = plugin_registry.emit_hook(data.hook_name, data.data)
    return {"hook": data.hook_name, "results": results}

# Add to main.py:
# from api.plugins import router as plugin_router
# app.include_router(plugin_router, prefix="/plugins", tags=["Plugin Marketplace"])