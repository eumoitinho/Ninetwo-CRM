"""
Kafka Service

Service for producing events to Confluent Cloud (Kafka).
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

from app.config import settings


class KafkaService:
    """
    Service class for producing events to Confluent Cloud (Kafka).

    Handles event streaming for leads, insights, and other CRM events.
    """

    def __init__(self):
        """Initialize Kafka producer"""
        self.producer: Optional[Producer] = None
        self._connected = False

    def connect(self):
        """
        Initialize Kafka producer with Confluent Cloud configuration.
        """
        try:
            logger.info("Connecting to Confluent Cloud (Kafka)...")

            # Producer configuration for Confluent Cloud
            config = {
                'bootstrap.servers': settings.kafka_bootstrap_servers,
                'security.protocol': settings.kafka_security_protocol,
                'sasl.mechanism': settings.kafka_sasl_mechanism,
                'sasl.username': settings.kafka_sasl_username,
                'sasl.password': settings.kafka_sasl_password,

                # Producer-specific configs
                'client.id': 'google-crm-integration',
                'acks': 'all',  # Wait for all replicas
                'compression.type': 'snappy',  # Compress messages
                'linger.ms': 10,  # Batch messages for efficiency
                'batch.size': 32768,  # 32KB batch size
                'max.in.flight.requests.per.connection': 5,
                'enable.idempotence': True,  # Exactly-once semantics
            }

            self.producer = Producer(config)
            self._connected = True

            logger.info("Successfully connected to Confluent Cloud")

        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            raise

    def disconnect(self):
        """Disconnect from Kafka and flush pending messages"""
        if self.producer:
            logger.info("Flushing pending Kafka messages...")
            self.producer.flush(timeout=30)
            self._connected = False
            logger.info("Disconnected from Kafka")

    def _delivery_callback(self, err, msg):
        """
        Callback function for message delivery reports.

        Args:
            err: Error if delivery failed
            msg: Message object
        """
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

    def _serialize_value(self, value: Any) -> bytes:
        """
        Serialize value to JSON bytes.

        Args:
            value: Value to serialize

        Returns:
            JSON bytes
        """
        # Convert datetime objects to ISO format
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(value, default=json_serial).encode('utf-8')

    def produce_event(
        self,
        topic: str,
        key: str,
        value: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Produce an event to Kafka topic.

        Args:
            topic: Kafka topic name
            key: Message key (for partitioning)
            value: Message value (will be JSON serialized)
            headers: Optional message headers
        """
        if not self._connected:
            raise RuntimeError("Not connected to Kafka. Call connect() first.")

        try:
            # Prepare headers
            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]

            # Add timestamp to value
            value['_kafka_timestamp'] = datetime.utcnow().isoformat()

            # Produce message
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8'),
                value=self._serialize_value(value),
                headers=kafka_headers,
                callback=self._delivery_callback
            )

            # Trigger delivery reports
            self.producer.poll(0)

            logger.debug(f"Produced event to topic {topic} with key {key}")

        except Exception as e:
            logger.error(f"Failed to produce event: {str(e)}")
            raise

    # ===== Convenience Methods for Specific Event Types =====

    def produce_lead_event(self, lead: Dict[str, Any], event_type: str = "lead.created"):
        """
        Produce a lead event.

        Args:
            lead: Lead data
            event_type: Event type (e.g., 'lead.created', 'lead.updated')
        """
        event = {
            'event_type': event_type,
            'event_time': datetime.utcnow().isoformat(),
            'lead': lead
        }

        self.produce_event(
            topic=settings.kafka_topic_leads,
            key=lead.get('id', 'unknown'),
            value=event,
            headers={'event_type': event_type}
        )

        logger.info(f"Produced lead event: {event_type} for lead {lead.get('id')}")

    def produce_insight_event(self, insight: Dict[str, Any], event_type: str = "insight.created"):
        """
        Produce an insight event.

        Args:
            insight: Insight data
            event_type: Event type (e.g., 'insight.created', 'insight.updated')
        """
        event = {
            'event_type': event_type,
            'event_time': datetime.utcnow().isoformat(),
            'insight': insight
        }

        self.produce_event(
            topic=settings.kafka_topic_insights,
            key=insight.get('id', 'unknown'),
            value=event,
            headers={'event_type': event_type}
        )

        logger.info(f"Produced insight event: {event_type} for insight {insight.get('id')}")

    def produce_custom_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        key: Optional[str] = None
    ):
        """
        Produce a custom CRM event.

        Args:
            event_type: Type of event
            data: Event data
            key: Optional message key (defaults to event_type)
        """
        event = {
            'event_type': event_type,
            'event_time': datetime.utcnow().isoformat(),
            'data': data
        }

        self.produce_event(
            topic=settings.kafka_topic_events,
            key=key or event_type,
            value=event,
            headers={'event_type': event_type}
        )

        logger.info(f"Produced custom event: {event_type}")

    def flush(self, timeout: float = 10.0):
        """
        Flush pending messages.

        Args:
            timeout: Maximum time to wait in seconds
        """
        if self.producer:
            remaining = self.producer.flush(timeout=timeout)
            if remaining > 0:
                logger.warning(f"{remaining} messages still pending after flush timeout")
            else:
                logger.info("All messages successfully flushed")


# Global instance
kafka_service = KafkaService()
