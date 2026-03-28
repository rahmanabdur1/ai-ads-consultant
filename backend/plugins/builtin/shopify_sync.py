# backend/plugins/builtin/shopify_sync.py

import httpx

class ShopifySyncPlugin:
    def __init__(self, config: dict):
        self.shop_url = config["shop_url"].rstrip("/")
        self.api_key = config["api_key"]
        self.headers = {"X-Shopify-Access-Token": self.api_key}

    def on_install(self):
        products = self.fetch_products(limit=1)
        return {"connected": True, "sample_products": len(products)}

    def fetch_products(self, limit: int = 10) -> list:
        url = f"{self.shop_url}/admin/api/2024-01/products.json?limit={limit}"
        res = httpx.get(url, headers=self.headers, timeout=10)
        res.raise_for_status()
        return res.json().get("products", [])

    def products_to_ad_brief(self, products: list) -> str:
        lines = []
        for p in products:
            title = p.get("title", "")
            price = p.get("variants", [{}])[0].get("price", "")
            desc = p.get("body_html", "").replace("<br>", " ").replace("<p>", "").replace("</p>", " ")[:200]
            tags = p.get("tags", "")
            lines.append(f"Product: {title} | Price: ${price} | Tags: {tags} | Info: {desc}")
        return "\n".join(lines)

    def on_campaign_launched(self, data: dict):
        try:
            products = self.fetch_products(limit=5)
            brief = self.products_to_ad_brief(products)
            return {"products_synced": len(products), "brief_preview": brief[:300]}
        except Exception as e:
            return {"error": str(e)}