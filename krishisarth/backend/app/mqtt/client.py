import json
import logging
import re
import asyncio
import paho.mqtt.client as mqtt
from app.core.config import settings
from app.db.redis import redis_client
from datetime import datetime, timezone
from app.mqtt import topics, handlers

logger = logging.getLogger(__name__)

# Topic Regex Patterns for Routing
RE_SOIL = re.compile(r"krishisarth/zone/([^/]+)/soil")
RE_AMBIENT = re.compile(r"krishisarth/zone/([^/]+)/ambient")
RE_PUMP_TEL = re.compile(r"krishisarth/zone/([^/]+)/pump/telemetry")

class MQTTClient:
    """
    Main MQTT Manager for KrishiSarth.
    Handles autonomous ingestion, validation, and failover via DLQ.
    """
    def __init__(self):
        self.client = mqtt.Client(client_id="krishisarth_backend_service")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT Subscriber Connected Successfully")
            client.subscribe(topics.WILDCARD)
        else:
            logger.error(f"MQTT Connection Failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"MQTT Disconnected (code {rc}). Attempting auto-reconnect...")

    def on_message(self, client, userdata, msg):
        """Dispatch incoming messages to the appropriate handlers."""
        payload_str = msg.payload.decode()
        try:
            payload = json.loads(payload_str)
            topic = msg.topic
            logger.debug(f"Received MQTT: {topic}")

            # Route 1: Soil Readings
            match_soil = RE_SOIL.match(topic)
            if match_soil:
                zone_id = match_soil.group(1)
                asyncio.run(handlers.handle_soil_reading(zone_id, payload))
                return

            # Route 2: Ambient Readings
            match_ambient = RE_AMBIENT.match(topic)
            if match_ambient:
                zone_id = match_ambient.group(1)
                asyncio.run(handlers.handle_ambient_reading(zone_id, payload))
                return

            # Route 3: Pump Telemetry
            match_pump = RE_PUMP_TEL.match(topic)
            if match_pump:
                zone_id = match_pump.group(1)
                asyncio.run(handlers.handle_pump_telemetry(zone_id, payload))
                return

        except Exception as e:
            self._send_to_dlq(msg.topic, payload_str, str(e))

    def _send_to_dlq(self, topic: str, payload: str, error: str):
        """Store failed messages in Redis for later analysis."""
        from app.db.redis import redis_client # Directly use global client if available
        logger.error(f"MQTT Processing Error on {topic}: {error}")
        try:
            dlq_item = {
                "topic": topic,
                "payload": payload,
                "error": error,
                "at": datetime.now(timezone.utc).isoformat()
            }
            redis_client.rpush("mqtt_dlq", json.dumps(dlq_item))
        except Exception as p_err:
            logger.critical(f"MQTT DLQ CRITICAL FAILURE: {str(p_err)}")

    def start(self):
        """Start the persistent MQTT loop."""
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            logger.info(f"MQTT Broker Listening on {settings.MQTT_BROKER_HOST}")
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.client.disconnect()

# Compatibility instance for publishing (Control logic)
mqtt_manager = MQTTClient()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mqtt_manager.start()
