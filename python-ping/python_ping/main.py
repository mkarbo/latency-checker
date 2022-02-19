import os
from datetime import datetime
from pythonping import ping
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteApi
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

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


def write_point(
    write_api: WriteApi, hostname: str, domain_tag: str, host_type: str
) -> Point:
    assert isinstance(write_api, WriteApi)
    point = get_ping_stats(hostname, domain_tag, host_type)
    assert isinstance(point, Point)
    try:
        write_api.write(bucket, org, point)
        return point
    except Exception as e:
        raise e


with InfluxDBClient(url=url, token=token, org=org) as client:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    with ThreadPoolExecutor(max_workers=4) as executor:
        while True:
            try:
                sleep(1)
                google_future = executor.submit(
                    write_point,
                    write_api=write_api,
                    hostname="8.8.8.8",
                    domain_tag="Google",
                    host_type="IP",
                )
                cloudflare_future = executor.submit(
                    write_point,
                    write_api=write_api,
                    hostname="1.1.1.1",
                    domain_tag="Cloudflare",
                    host_type="IP",
                )
                for future in as_completed([google_future, cloudflare_future]):
                    exception = future.exception()
                    if exception is not None:
                        raise exception
                    point = future.result()
                    logging.info(point.to_line_protocol())
            except Exception as e:
                logging.exception(e)
                sleep(1)
