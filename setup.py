#!/usr/bin/env python3
"""
Simple CSV Creator
Creates products.csv and policies.csv
"""

import os

def create_csv_files():
    """Create CSV files with sample data"""
    
    # Create data folder if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # ========================================================================
    # PRODUCTS CSV
    # ========================================================================
    products_data = """name,description,price,category,stock,brand,features,warranty
SoundPro Wireless Headphones,Premium wireless headphones with active noise cancellation and 30-hour battery life. Features Bluetooth 5.0 connectivity and comfortable over-ear design,89.99,audio,50,SoundPro,noise-cancelling|bluetooth|30h-battery|over-ear,2-year
BudMax Sport Earbuds,Waterproof IPX7 sport earbuds with secure fit and sweat resistance. Perfect for workouts with 8-hour battery life,59.99,audio,100,BudMax,waterproof|sport|8h-battery|secure-fit,1-year
SmartFit Fitness Tracker,Advanced fitness tracker with heart rate monitoring and sleep tracking. Includes GPS and 7-day battery life,79.99,wearables,75,SmartFit,heart-rate|sleep-tracking|gps|7-day-battery,1-year
PowerBank Pro 20000mAh,High-capacity portable charger with fast charging support. Dual USB ports and LED battery display,49.99,accessories,120,PowerBank,20000mah|fast-charging|dual-usb|led-display,2-year
UltraView 4K Webcam,Professional 4K webcam with auto-focus and low-light correction. Built-in dual microphones for clear audio,129.99,electronics,40,UltraView,4k|auto-focus|dual-mic|low-light,1-year
QuickCharge USB-C Cable,Premium USB-C charging cable with reinforced connectors. Supports fast charging up to 100W,19.99,accessories,200,QuickCharge,usb-c|fast-charging|100w|reinforced,lifetime
GamePad Pro Controller,Wireless gaming controller with haptic feedback and programmable buttons. Compatible with PC and mobile,69.99,gaming,60,GamePad,wireless|haptic|programmable|multi-platform,1-year
SmartHome Hub Max,Central smart home controller with voice assistant integration. Controls lights and appliances and security devices,149.99,smart-home,30,SmartHome,voice-control|hub|automation|security,2-year
PortaScreen Portable Monitor,15.6-inch portable monitor with USB-C connectivity. Perfect for remote work with 1080p display,199.99,electronics,25,PortaScreen,15.6-inch|usb-c|1080p|portable,1-year
AirPure Mini Air Purifier,Compact air purifier with HEPA filter and quiet operation. Covers rooms up to 200 square feet,89.99,home,45,AirPure,hepa-filter|quiet|200sqft|compact,1-year
EcoBottle Smart Water Bottle,Smart water bottle with hydration tracking and temperature display. Keeps drinks cold for 24 hours,34.99,lifestyle,80,EcoBottle,smart-tracking|temperature-display|24h-cold|eco-friendly,1-year
FlexDesk Standing Desk,Adjustable standing desk with electric height control. Features memory presets and cable management,399.99,furniture,15,FlexDesk,electric|adjustable|memory-presets|cable-management,5-year
LumiLight Smart Bulb,WiFi-enabled smart bulb with 16 million colors and voice control. Energy efficient LED technology,24.99,smart-home,150,LumiLight,wifi|16m-colors|voice-control|energy-efficient,2-year
ProClean Robot Vacuum,Smart robot vacuum with mapping and scheduled cleaning. Works with Alexa and Google Home,299.99,home,20,ProClean,mapping|scheduled-cleaning|voice-compatible|smart-navigation,2-year
SecureCam Indoor Camera,1080p indoor security camera with night vision and two-way audio. Motion detection alerts,79.99,security,55,SecureCam,1080p|night-vision|two-way-audio|motion-detection,1-year"""

    with open("data/products.csv", "w") as f:
        f.write(products_data)
    
    print("✅ Created: data/products.csv")
    print("   - 15 products loaded")
    
    # ========================================================================
    # POLICIES CSV
    # ========================================================================
    policies_data = """category,question,answer
shipping,What are your shipping options?,We offer free standard shipping on orders over $50. Standard shipping takes 5-7 business days and costs $5.99. Express shipping is available for $12.99 and takes 2-3 business days. Next-day shipping is $24.99 for orders placed before 2pm EST.
returns,What is your return policy?,We offer a 30-day return policy on all products. Items must be unused and in original packaging. Return shipping is free for defective items. Refunds are processed within 5-7 business days of receiving the returned item.
warranty,What warranty do you provide?,Most products come with a 1-2 year manufacturer warranty covering manufacturing defects. Extended warranty options are available at checkout. Warranty does not cover accidental damage or normal wear and tear.
payment,What payment methods do you accept?,We accept all major credit cards including Visa MasterCard American Express and Discover. We also accept PayPal Apple Pay Google Pay and Venmo. All transactions are secure and encrypted with SSL.
tracking,How can I track my order?,Once your order ships you will receive a tracking number via email and SMS. You can track your package on our website by entering your order number or directly on the carrier's website using the tracking number provided.
cancellation,Can I cancel my order?,Orders can be cancelled within 24 hours of placement while in pending status. After the order enters processing it cannot be cancelled. If you need to cancel please contact support immediately at 1-800-SUPPORT.
support,How do I contact customer support?,You can reach our support team via email at support@store.com phone at 1-800-SUPPORT or through live chat on our website. Live chat is available Monday through Friday 9am to 6pm EST. We respond to emails within 24 hours.
stock,What if an item is out of stock?,Out of stock items can be backordered and you will be notified when they become available. We also offer email notifications when items are back in stock. Our team can suggest similar in-stock alternatives.
discount,Do you offer any discounts?,We offer a 10% discount for first-time customers using code WELCOME10. Students and military personnel receive 15% off with verification. We also run seasonal sales and send exclusive deals to email subscribers.
international,Do you ship internationally?,We currently ship to the United States Canada and Mexico. International shipping rates vary by location and are calculated at checkout. Customs duties and taxes are the responsibility of the customer.
gift,Can I send items as gifts?,Yes! We offer gift wrapping for $4.99 per item and can include a personalized message. Gift recipients won't see prices on the packing slip. We also offer e-gift cards in any amount.
bulk,Do you offer bulk pricing?,Yes we offer discounts for bulk orders of 10 or more units. Please contact our business sales team at business@store.com for custom quotes. Corporate accounts are available with net-30 payment terms."""

    with open("data/policies.csv", "w") as f:
        f.write(policies_data)
    
    print("✅ Created: data/policies.csv")
    print("   - 12 FAQ items loaded")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  CSV File Creator")
    print("="*60 + "\n")
    
    create_csv_files()
    
    print("\n" + "="*60)
    print("✅ Done! CSV files created in 'data/' folder")
    print("="*60 + "\n")