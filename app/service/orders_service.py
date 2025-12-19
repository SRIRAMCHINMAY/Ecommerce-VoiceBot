import pandas as pd
from typing import Optional, Dict, List
import os

class OrderService:
    """Order service that loads from CSV"""
    
    def __init__(self, csv_path: str = "./data/orders.csv"):
        """
        Initialize order service from CSV
        
        Args:
            csv_path: Path to orders CSV file
        """
        self.orders = {}
        self.csv_path = csv_path
        
        if os.path.exists(csv_path):
            self._load_orders_from_csv()
        else:
            print(f"⚠️  Orders CSV not found at {csv_path}")
    
    def _load_orders_from_csv(self):
        """Load orders from CSV file"""
        try:
            df = pd.read_csv(self.csv_path)
            
            for _, row in df.iterrows():
                order_id = row['order_id']
                
                # Parse items (format: "Product x2, Product2 x1")
                items = []
                if pd.notna(row['items']):
                    items_str = str(row['items'])
                    # Split by commas or common separators
                    item_parts = items_str.split(',') if ',' in items_str else [items_str]
                    
                    for item_part in item_parts:
                        item_part = item_part.strip()
                        # Try to extract quantity (e.g., "Product x2")
                        if ' x' in item_part:
                            name, qty = item_part.rsplit(' x', 1)
                            try:
                                quantity = int(qty)
                            except:
                                quantity = 1
                            items.append({"name": name.strip(), "quantity": quantity})
                        else:
                            items.append({"name": item_part, "quantity": 1})
                
                # Build order object
                order = {
                    "order_id": order_id,
                    "customer_name": str(row['customer_name']) if pd.notna(row['customer_name']) else "",
                    "status": str(row['status']).lower() if pd.notna(row['status']) else "unknown",
                    "items": items,
                    "total": float(row['total']) if pd.notna(row['total']) else 0.0,
                    "order_date": str(row['order_date']) if pd.notna(row['order_date']) else "",
                    "shipping_address": str(row['shipping_address']) if pd.notna(row['shipping_address']) else "",
                    "estimated_delivery": str(row['estimated_delivery']) if pd.notna(row['estimated_delivery']) else ""
                }
                
                # Optional fields
                if pd.notna(row.get('tracking_number')):
                    order["tracking_number"] = str(row['tracking_number'])
                
                if pd.notna(row.get('carrier')):
                    order["carrier"] = str(row['carrier'])
                
                if pd.notna(row.get('delivered_date')):
                    order["delivered_date"] = str(row['delivered_date'])
                
                if pd.notna(row.get('cancelled_date')):
                    order["cancelled_date"] = str(row['cancelled_date'])
                
                if pd.notna(row.get('cancellation_reason')):
                    order["cancellation_reason"] = str(row['cancellation_reason'])
                
                self.orders[order_id] = order
            
            print(f"✅ Loaded {len(self.orders)} orders from CSV")
        
        except Exception as e:
            print(f"❌ Error loading orders: {e}")
    
    def track_order(self, order_id: str) -> Optional[Dict]:
        """Track order by ID"""
        # Normalize order ID (case-insensitive, remove spaces)
        order_id = order_id.upper().replace(" ", "")
        
        if order_id in self.orders:
            return self.orders[order_id]
        return None
    
    def get_order_status(self, order_id: str) -> Optional[str]:
        """Get just the status of an order"""
        order = self.track_order(order_id)
        return order["status"] if order else None
    
    def get_all_orders(self) -> List[Dict]:
        """Get all orders"""
        return list(self.orders.values())
    
    def search_orders_by_customer(self, customer_name: str) -> List[Dict]:
        """Search orders by customer name (partial match)"""
        customer_name = customer_name.lower()
        results = []
        
        for order_id, order in self.orders.items():
            if customer_name in order["customer_name"].lower():
                results.append(order)
        
        return results