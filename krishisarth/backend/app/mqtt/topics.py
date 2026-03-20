# KrishiSarth MQTT Topic Constants (PROJECT_RULES.md 9.4)

# Wildcard Subscription
WILDCARD = "krishisarth/#"

# Sensor Data Ingestion
SOIL_READINGS = "krishisarth/zone/+/soil"
AMBIENT_READINGS = "krishisarth/zone/+/ambient"
PUMP_TELEMETRY = "krishisarth/zone/+/pump/telemetry"
GATEWAY_STATUS = "krishisarth/gateway/+/status"

# Control Commands (Publish)
PUMP_ON = "krishisarth/zone/{zone_id}/pump/on"
PUMP_OFF = "krishisarth/zone/{zone_id}/pump/off"

# Control Feedback (Subscribe)
PUMP_ACK = "krishisarth/zone/+/pump/ack"

# System Alerts
SYSTEM_ALERT = "krishisarth/system/alert"
