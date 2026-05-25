from adaptive_backend.services.realtime.websocket_manager import ConnectionManager
from adaptive_backend.services.realtime.monitoring_service import RealTimeMonitoringService


ws_manager = ConnectionManager()
monitoring_service = RealTimeMonitoringService(ws_manager)
