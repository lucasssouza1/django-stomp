import json
import logging
import ssl
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Callable
from typing import Dict

import stomp

logger = logging.getLogger(__name__)


class Acknowledgements(Enum):
    """
    See more details at:
        - https://pubsub.github.io/pubsub-specification-1.2.html#SUBSCRIBE_ack_Header
        - https://jasonrbriggs.github.io/pubsub.py/api.html#acks-and-nacks
    """

    CLIENT = "client"
    CLIENT_INDIVIDUAL = "client-individual"
    AUTO = "auto"


@dataclass(frozen=True)
class Payload:
    ack: Callable
    nack: Callable
    headers: Dict
    body: Dict


class _Listener(stomp.ConnectionListener):
    def __init__(
        self,
        connection: stomp.StompConnection11,
        callback: Callable,
        subscription_configuration: Dict,
        connection_configuration: Dict,
    ) -> None:
        self._subscription_configuration = subscription_configuration
        self._connection_configuration = connection_configuration
        self._connection = connection
        self._callback: Callable = callback
        self._subscription_id = str(uuid.uuid4())
        self._listener_id = str(uuid.uuid4())

    def on_message(self, headers, message):
        message_id = headers["message-id"]
        logger.info(f"Message ID: {message_id}")
        logger.debug("Received headers: %s", headers)
        logger.debug("Received message: %s", message)

        # https://jasonrbriggs.github.io/stomp.py/api.html#acks-and-nacks
        def ack_logic():
            self._connection.ack(message_id, self._subscription_id)

        def nack_logic():
            self._connection.nack(message_id, self._subscription_id)

        self._callback(Payload(ack_logic, nack_logic, headers, json.loads(message)))

    def is_open(self):
        return self._connection.is_connected()

    def start(self, wait_forever=True):
        logger.info(f"Starting listener with name: {self._listener_id}")
        logger.info(f"Subscribe/Listener auto-generated ID: {self._subscription_id}")

        self._connection.set_listener(self._listener_id, self)
        self._connection.start()
        self._connection.connect(**self._connection_configuration)
        self._connection.subscribe(id=self._subscription_id, **self._subscription_configuration)
        logger.info("Connected")
        if wait_forever:
            while True:
                if not self.is_open():
                    logger.info("It is not open. Starting...")
                    self.start(wait_forever=False)
                time.sleep(1)

    def close(self):
        self._connection.disconnect()
        logger.info("Disconnected")


def build_listener(destination_name, callback, ack_type=Acknowledgements.CLIENT, **connection_params) -> _Listener:
    logger.info("Building listener...")
    hosts = [(connection_params.get("host"), connection_params.get("port"))]
    use_ssl = connection_params.get("use_ssl", False)
    ssl_version = connection_params.get("ssl_version", ssl.PROTOCOL_TLS)
    logger.info(f"Use SSL? {use_ssl}. Version: {ssl_version}")
    # http://stomp.github.io/stomp-specification-1.2.html#Heart-beating
    conn = stomp.Connection(hosts, ssl_version=ssl_version, use_ssl=use_ssl)
    client_id = connection_params.get("client_id", uuid.uuid4())
    subscription_configuration = {"destination": destination_name, "ack": ack_type.value}
    connection_configuration = {
        "username": connection_params.get("username"),
        "passcode": connection_params.get("password"),
        "wait": True,
        "headers": {"client-id": f"{client_id}-listener", "activemq.prefetchSize": 1},
    }
    listener = _Listener(conn, callback, subscription_configuration, connection_configuration)
    return listener
