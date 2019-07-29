import random
import socket
from logging import Logger
from typing import Tuple

from esper.ext.forwarder import TCPForwarder


class Relay(object):
    """
    A Local TCP relay to stream data between ADB Client and TCP relay.
    Data streaming is implemented using 2 threads, one for each direction.
    """

    listener_host = '127.0.0.1'
    listener_port = None
    _listener_server = None
    listener_timeout = 5 * 60

    forward = None
    reverse = None

    inbound_conn = None
    inbound_addr = None
    outbound_conn = None
    outbound_addr = None

    started = None
    stopped = None

    timeout = 30 * 60  # 30 mins, same as TCP relay

    log = None

    def __init__(self,
                 relay_conn: socket.socket = None,
                 relay_addr: Tuple[str, int] = (None, None),
                 log: Logger = None):

        self.log = log
        self.outbound_conn = relay_conn
        self.outbound_addr = relay_addr

        self.listener_port = self.get_random_port()

        self.setup_listener()

    def get_random_port(self, min_port=47000, max_port=57000) -> int:
        '''Iterate over a range of ports and pick the first free port and return it '''

        for count in range((max_port - min_port)):
            port = random.randrange(min_port, max_port)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                resp = probe.connect_ex((socket.gethostname(), port))
                if resp != 0:
                    return port

    def get_listener_address(self) -> Tuple[str, int]:
        return self.listener_host, self.listener_port

    def setup_listener(self) -> None:
        # Setup a TCP Socket Listener
        self._listener_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener_server.bind(self.get_listener_address())
        self._listener_server.listen(1)

    def accept_connection(self) -> Tuple[socket.socket, Tuple[str, int]]:
        # Accept 2 Connections on the Listener;
        # one for device, and one for ADB client
        self._listener_server.settimeout(self.listener_timeout)
        conn, addr = self._listener_server.accept()

        self.log.debug(f"Connection accepted from ADB Client: {addr[0]}:{addr[1]}")

        self.log.debug(f"Closing Listener on Port : {self.listener_port}")
        self._listener_server.close()

        self.inbound_conn = conn
        self.inbound_addr = addr

        return conn, addr

    def gather_metrics(self):
        if self.forward.connection_started and self.reverse.connection_started:
            self.started = min(self.forward.connection_started, self.reverse.connection_started)
        else:
            self.started = self.forward.connection_started or self.reverse.connection_started

        if self.forward.connection_stopped and self.reverse.connection_stopped:
            self.stopped = max(self.forward.connection_stopped, self.reverse.connection_stopped)
        else:
            self.stopped = self.forward.connection_stopped or self.reverse.connection_stopped

        self.log.debug(f"Relay started: {self.started.isoformat()}")
        self.log.debug(f"Relay stopped: {self.stopped.isoformat()}")
        self.log.debug(f"Relay Session duration: {str(self.stopped - self.started)}")

        return {
            "started": self.started,
            "stopped": self.stopped,
            "bytes": max(self.forward.bytes, self.reverse.bytes)
        }

    def start_relay(self):

        # Starting forward traffic
        self.forward = TCPForwarder(inbound_conn=self.inbound_conn, inbound_address=self.inbound_addr,
                                    outbound_conn=self.outbound_conn, outbound_address=self.outbound_addr, log=self.log)

        # Starting reverse traffic
        self.reverse = TCPForwarder(inbound_conn=self.outbound_conn, inbound_address=self.outbound_addr,
                                    outbound_conn=self.inbound_conn, outbound_address=self.inbound_addr, log=self.log)

        self.forward.start()
        self.reverse.start()

        self.forward.join(self.timeout)
        self.reverse.join(self.timeout)

    def stop_relay(self):

        self.log.debug(f"Killing Forward Thread")
        self.forward.stop()
        self.forward.join(timeout=1)

        self.log.debug(f"Killing Reverse Thread...")
        self.reverse.stop()
        self.reverse.join(timeout=1)

    def cleanup_connections(self):
        self.inbound_conn.close()
        self.outbound_conn.close()

    def run_forever(self):
        try:
            self.start_relay()
            self.log.info("Forwarder Threads Timed out!")

        except KeyboardInterrupt:
            self.log.info("Encountered KeyboardInterrupt! Quitting...")

        except:
            self.log.exception("Unhandled Exception!")

        finally:
            self.log.info("Closing remaining Sockets...")

            self.stop_relay()

            self.gather_metrics()

            self.cleanup_connections()
