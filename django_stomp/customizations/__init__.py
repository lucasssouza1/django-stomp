from stomp import connect
from stomp.constants import CMD_NACK
from stomp.constants import HDR_MESSAGE_ID
from stomp.constants import HDR_SUBSCRIPTION
from stomp.constants import HDR_TRANSACTION
from stomp.transport import DEFAULT_SSL_VERSION


class CustomStompConnection11(connect.StompConnection11):
    def __init__(
        self,
        host_and_ports=None,
        prefer_localhost=True,
        try_loopback_connect=True,
        reconnect_sleep_initial=0.1,
        reconnect_sleep_increase=0.5,
        reconnect_sleep_jitter=0.1,
        reconnect_sleep_max=60.0,
        reconnect_attempts_max=3,
        use_ssl=False,
        ssl_key_file=None,
        ssl_cert_file=None,
        ssl_ca_certs=None,
        ssl_cert_validator=None,
        wait_on_receipt=False,
        ssl_version=DEFAULT_SSL_VERSION,
        timeout=None,
        heartbeats=(0, 0),
        keepalive=None,
        vhost=None,
        auto_decode=True,
        auto_content_length=True,
    ):
        super().__init__(
            host_and_ports,
            prefer_localhost,
            try_loopback_connect,
            reconnect_sleep_initial,
            reconnect_sleep_increase,
            reconnect_sleep_jitter,
            reconnect_sleep_max,
            reconnect_attempts_max,
            use_ssl,
            ssl_key_file,
            ssl_cert_file,
            ssl_ca_certs,
            ssl_cert_validator,
            wait_on_receipt,
            ssl_version,
            timeout,
            heartbeats,
            keepalive,
            vhost,
            auto_decode,
            auto_content_length,
        )

    def nack(self, id, subscription, transaction=None, requeue=False):
        assert id is not None, "'id' is required"
        assert subscription is not None, "'subscription' is required"
        headers = {HDR_MESSAGE_ID: id, HDR_SUBSCRIPTION: subscription}
        # Because of RabbitMQ: https://www.rabbitmq.com/stomp.html#ack-nack
        if requeue:
            headers.update({"requeue": "true"})
        else:
            headers.update({"requeue": "false"})
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_NACK, headers)