# backend/core/plugin_registry.py

import importlib
import os
import json
from typing import Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PluginMeta:
    id: str
    name: str
    version: str
    description: str
    author: str
    category: str        # analytics / creative / targeting / automation / integration
    entry_point: str     # module.ClassName
    config_schema: dict  # JSON schema for plugin config
    is_active: bool = False
    installed_at: datetime = field(default_factory=datetime.utcnow)

class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, PluginMeta] = {}
        self._instances: Dict[str, Any] = {}
        self._hooks: Dict[str, list] = {}
        self._load_builtin_plugins()

    def _load_builtin_plugins(self):
        builtin = [
            PluginMeta(
                id="slack_notifier",
                name="Slack Notifier",
                version="1.0.0",
                description="Send campaign alerts and reports to Slack channels",
                author="AI Ads Core",
                category="integration",
                entry_point="plugins.builtin.slack_notifier.SlackNotifierPlugin",
                config_schema={
                    "webhook_url": {"type": "string", "required": True},
                    "channel": {"type": "string", "default": "#ads-alerts"},
                    "notify_on": {"type": "array", "default": ["campaign_launched", "optimization_done", "ab_winner"]}
                }
            ),
            PluginMeta(
                id="shopify_sync",
                name="Shopify Sync",
                version="1.0.0",
                description="Pull product data from Shopify to auto-generate ad copy",
                author="AI Ads Core",
                category="integration",
                entry_point="plugins.builtin.shopify_sync.ShopifySyncPlugin",
                config_schema={
                    "shop_url": {"type": "string", "required": True},
                    "api_key": {"type": "string", "required": True},
                    "sync_interval_hours": {"type": "integer", "default": 6}
                }
            ),
            PluginMeta(
                id="report_generator",
                name="PDF Report Generator",
                version="1.0.0",
                description="Auto-generate weekly PDF performance reports",
                author="AI Ads Core",
                category="analytics",
                entry_point="plugins.builtin.report_generator.ReportGeneratorPlugin",
                config_schema={
                    "email": {"type": "string", "required": True},
                    "schedule": {"type": "string", "default": "weekly"},
                    "include_sections": {"type": "array", "default": ["summary", "campaigns", "recommendations"]}
                }
            ),
            PluginMeta(
                id="audience_expander",
                name="AI Audience Expander",
                version="1.0.0",
                description="Automatically suggests lookalike and interest audiences using AI",
                author="AI Ads Core",
                category="targeting",
                entry_point="plugins.builtin.audience_expander.AudienceExpanderPlugin",
                config_schema={
                    "min_audience_size": {"type": "integer", "default": 10000},
                    "expansion_factor": {"type": "number", "default": 1.5},
                    "platforms": {"type": "array", "default": ["meta", "google"]}
                }
            ),
            PluginMeta(
                id="creative_ai",
                name="Creative AI Generator",
                version="1.0.0",
                description="Generate image prompts and creative briefs using DALL-E",
                author="AI Ads Core",
                category="creative",
                entry_point="plugins.builtin.creative_ai.CreativeAIPlugin",
                config_schema={
                    "style": {"type": "string", "default": "photorealistic"},
                    "aspect_ratio": {"type": "string", "default": "1:1"},
                    "brand_colors": {"type": "array", "default": []}
                }
            ),
            PluginMeta(
                id="whatsapp_notifier",
                name="WhatsApp Notifier",
                version="1.0.0",
                description="Send campaign updates via WhatsApp Business API",
                author="AI Ads Core",
                category="integration",
                entry_point="plugins.builtin.whatsapp_notifier.WhatsAppPlugin",
                config_schema={
                    "phone_number_id": {"type": "string", "required": True},
                    "access_token": {"type": "string", "required": True},
                    "recipient": {"type": "string", "required": True}
                }
            ),
        ]
        for plugin in builtin:
            self._plugins[plugin.id] = plugin

    def list_plugins(self, category: str = None) -> list:
        plugins = list(self._plugins.values())
        if category:
            plugins = [p for p in plugins if p.category == category]
        return plugins

    def install_plugin(self, plugin_id: str, config: dict) -> dict:
        if plugin_id not in self._plugins:
            return {"success": False, "error": f"Plugin {plugin_id} not found"}
        plugin = self._plugins[plugin_id]
        errors = self._validate_config(plugin.config_schema, config)
        if errors:
            return {"success": False, "errors": errors}
        plugin.is_active = True
        try:
            instance = self._instantiate_plugin(plugin, config)
            self._instances[plugin_id] = instance
            if hasattr(instance, "on_install"):
                instance.on_install()
            return {"success": True, "plugin_id": plugin_id, "message": f"{plugin.name} installed successfully"}
        except Exception as e:
            plugin.is_active = False
            return {"success": False, "error": str(e)}

    def uninstall_plugin(self, plugin_id: str) -> dict:
        if plugin_id in self._instances:
            instance = self._instances[plugin_id]
            if hasattr(instance, "on_uninstall"):
                instance.on_uninstall()
            del self._instances[plugin_id]
        if plugin_id in self._plugins:
            self._plugins[plugin_id].is_active = False
        return {"success": True, "message": f"Plugin {plugin_id} uninstalled"}

    def emit_hook(self, hook_name: str, data: dict) -> list:
        results = []
        for plugin_id, instance in self._instances.items():
            if hasattr(instance, f"on_{hook_name}"):
                try:
                    result = getattr(instance, f"on_{hook_name}")(data)
                    results.append({"plugin": plugin_id, "result": result})
                except Exception as e:
                    results.append({"plugin": plugin_id, "error": str(e)})
        return results

    def _validate_config(self, schema: dict, config: dict) -> list:
        errors = []
        for key, rules in schema.items():
            if rules.get("required") and key not in config:
                errors.append(f"Missing required field: {key}")
        return errors

    def _instantiate_plugin(self, plugin: PluginMeta, config: dict):
        module_path, class_name = plugin.entry_point.rsplit(".", 1)
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return cls(config)
        except ImportError:
            return MockPlugin(plugin.name, config)

class MockPlugin:
    def __init__(self, name, config):
        self.name = name
        self.config = config
    def on_install(self): pass
    def on_campaign_launched(self, data): return f"{self.name}: acknowledged campaign launch"
    def on_optimization_done(self, data): return f"{self.name}: acknowledged optimization"
    def on_ab_winner(self, data): return f"{self.name}: acknowledged A/B winner"

plugin_registry = PluginRegistry()