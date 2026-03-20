r"""
KrishiSarth — Fake Sensor Data Injector
Run this to populate InfluxDB with realistic sensor data so the dashboard shows real values.
Usage: .\venv\Scripts\python.exe scripts\inject_fake_sensors.py
"""

import sys
import os
import random
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from app.core.config import settings
from app.db.postgres import SessionLocal
from app.models import Zone, Farm

def inject():
    db = SessionLocal()
    zones = db.query(Zone).all()
    farms = db.query(Farm).all()
    db.close()

    if not zones:
        print("ERROR: No zones found. Run seed.py first.")
        return

    client = InfluxDBClient(
        url=settings.INFLUXDB_URL,
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG
    )
    write_api = client.write_api(write_options=SYNCHRONOUS)
    now = datetime.now(timezone.utc)

    print(f"Injecting sensor data for {len(zones)} zones...\n")

    for zone in zones:
        zone_id = str(zone.id)
        moisture = round(random.uniform(15, 75), 1)
        temp     = round(random.uniform(25, 38), 1)
        ec       = round(random.uniform(0.8, 2.5), 2)
        ph       = round(random.uniform(6.0, 7.5), 1)

        soil_point = (
            Point("soil_readings")
            .tag("zone_id", zone_id)
            .tag("device_id", f"ESP32-{zone_id[:8]}")
            .tag("depth", "0-15cm")
            .field("moisture_pct", moisture)
            .field("temp_c", temp)
            .field("ec_ds_m", ec)
            .field("ph", ph)
            .time(now, WritePrecision.NS)
        )
        write_api.write(
            bucket=settings.INFLUXDB_BUCKET,
            org=settings.INFLUXDB_ORG,
            record=soil_point
        )
        print(f"  Zone '{zone.name}': moisture={moisture}%  temp={temp}C  EC={ec}  pH={ph}")

    # Inject water quality for each farm
    for farm in farms:
        farm_id = str(farm.id)
        wq_point = (
            Point("water_quality")
            .tag("farm_id", farm_id)
            .tag("device_id", "WQ-SENSOR-01")
            .field("ph", round(random.uniform(6.5, 7.5), 1))
            .field("ec_ms_cm", round(random.uniform(1.0, 2.0), 2))
            .field("turbidity_ntu", round(random.uniform(1.0, 5.0), 1))
            .field("nitrate_ppm", round(random.uniform(10.0, 22.0), 1))
            .field("tank_level", round(random.uniform(40.0, 95.0), 1))
            .time(now, WritePrecision.NS)
        )
        write_api.write(
            bucket=settings.INFLUXDB_BUCKET,
            org=settings.INFLUXDB_ORG,
            record=wq_point
        )
        print(f"\n  Farm '{farm.name}': water quality injected")

    print("\nDone! Hard-refresh your dashboard (Ctrl+Shift+R) to see the data.")
    client.close()

if __name__ == "__main__":
    inject()
