import sys
import os
import bcrypt
from sqlalchemy.orm import Session

# Add the project root to sys.path for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres import SessionLocal
from app.models import Farmer, Farm, Zone, Device
from app.services import auth_service

def seed_data():
    """
    Populates the development database with realistic test data for a solo farmer.
    This script is idempotent and can be safely run multiple times.
    """
    db: Session = SessionLocal()
    try:
        print("--- Starting Database Seeding ---")
        
        # 1. Create Farmer
        farmer_email = "ramesh@krishisarth.com"
        farmer = db.query(Farmer).filter(Farmer.email == farmer_email).first()
        if not farmer:
            password = "Test@12345"
            # Use auth_service for hashing
            password_hash = auth_service.hash_password(password)
            
            farmer = Farmer(
                name="Ramesh Patil",
                email=farmer_email,
                phone="+919876543210",
                password_hash=password_hash,
                preferred_lang="mr"
            )
            db.add(farmer)
            db.commit()
            db.refresh(farmer)
            print(f"CREATED Farmer: {farmer.name} ({farmer_email})")
        else:
            print(f"EXISTS  Farmer: {farmer.name} ({farmer_email})")

        # 2. Create Farm
        farm_name = "Patil North Farm"
        farm = db.query(Farm).filter(Farm.name == farm_name, Farm.farmer_id == farmer.id).first()
        if not farm:
            farm = Farm(
                farmer_id=farmer.id,
                name=farm_name,
                soil_type="loamy",
                area_ha=4.5,
                lat=18.5204,
                lng=73.8567
            )
            db.add(farm)
            db.commit()
            db.refresh(farm)
            print(f"CREATED Farm: {farm.name}")
        else:
            print(f"EXISTS  Farm: {farm.name}")

        # 3. Create 6 Zones
        zones_data = [
            {"name": "Mango Grove", "crop": "mango", "stage": "flowering", "area": 15000},
            {"name": "Grape Vineyard", "crop": "grape", "stage": "fruiting", "area": 12000},
            {"name": "Tomato Patch", "crop": "tomato", "stage": "vegetative", "area": 5000},
            {"name": "Wheat Field", "crop": "wheat", "stage": "harvesting", "area": 8000},
            {"name": "Sugarcane Block", "crop": "sugarcane", "stage": "tillering", "area": 10000},
            {"name": "Mixed Veggie Garden", "crop": "mixed", "stage": "seedling", "area": 2000},
        ]

        for i, z_info in enumerate(zones_data, 1):
            zone = db.query(Zone).filter(Zone.name == z_info["name"], Zone.farm_id == farm.id).first()
            if not zone:
                zone = Zone(
                    farm_id=farm.id,
                    name=z_info["name"],
                    crop_type=z_info["crop"],
                    crop_stage=z_info["stage"],
                    area_sqm=z_info["area"],
                    is_active=True
                )
                db.add(zone)
                db.commit()
                db.refresh(zone)
                print(f"CREATED Zone: {zone.name}")
            else:
                print(f"EXISTS  Zone: {zone.name}")

            # 4. Create 2 Devices per Zone
            sensor_serial = f"ESP32-AQ-{i:03d}"
            pump_serial = f"PUMP-ACT-{i:03d}"
            
            # Sensor Node
            sensor = db.query(Device).filter(Device.serial_no == sensor_serial).first()
            if not sensor:
                sensor = Device(
                    zone_id=zone.id,
                    type="sensor",
                    serial_no=sensor_serial,
                    firmware_ver="1.0.4",
                    battery_pct=85,
                    is_online=True
                )
                db.add(sensor)
                print(f"  - CREATED Sensor Node: {sensor_serial}")
            else:
                print(f"  - EXISTS  Sensor Node: {sensor_serial}")
            
            # Pump Actuator
            pump = db.query(Device).filter(Device.serial_no == pump_serial).first()
            if not pump:
                pump = Device(
                    zone_id=zone.id,
                    type="actuator",
                    serial_no=pump_serial,
                    firmware_ver="1.1.0",
                    is_online=False
                )
                db.add(pump)
                print(f"  - CREATED Pump Actuator: {pump_serial}")
            else:
                print(f"  - EXISTS  Pump Actuator: {pump_serial}")
            
            db.commit()

        print("--- Database Seeding Completed Successfully ---")
    except Exception as e:
        print(f"CRITICAL ERROR during seeding: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
