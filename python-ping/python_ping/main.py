import os
from datetime import datetime
from pythonping import ping
from time import sleep

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


org = os.getenv("INFLUXDB_ORG", "my-org")
bucket = os.getenv("INFLUXDB_BUCKET", "my-bucket")
token = os.getenv("INFLUXDB_TOKEN")

host = os.getenv("INFLUXDB_HOSTNAME", "influxdb")
port = os.getenv("INFLUXDB_PORT", "8086")

machine_name = os.getenv("MACHINE_NAME", "docker")

# Only suitable for running this in a docker-compose setup.
# Consider changing the variable setup and hostname wrapper for deployment e.g., to k8s
url = f"http://{host}:{port}"
assert token is not None


def get_ping_stats(
    hostname: str, domain_tag: str, host_type: str, count: int = 4
) -> Point:
    res = ping(hostname, timeout=1, count=count)

    point = (
        Point("latency")
        .tag("machine", machine_name)
        .tag("hostname", hostname)
        .tag("domain_owner", domain_tag)
        .tag("host_type", host_type)
        .field("packet_loss", float(res.packet_loss))
        .field("packets_lost", int(res.packet_loss * count))
        .field("average_time", float(res.rtt_avg_ms))
        .field("max_time", float(res.rtt_max_ms))
        .field("min_time", float(res.rtt_min_ms))
        .field("any_lost", bool(res.packet_loss > 0))
        .time(datetime.utcnow(), WritePrecision.NS)
    )
    return point


with InfluxDBClient(url=url, token=token, org=org) as client:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    while True:
        try:
            sleep(1)
            point = get_ping_stats("8.8.8.8", "Google", "IP")
            write_api.write(bucket, org, point)
            point = get_ping_stats("1.1.1.1", "Cloudflare", "IP")
            write_api.write(bucket, org, point)
            print(point.to_line_protocol())
        except Exception as e:
            print(f"Caught exception: {e}")
            sleep(1)
