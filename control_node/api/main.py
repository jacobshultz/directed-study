import os

import grpc
from fastapi import FastAPI, HTTPException

import camera_pb2
import camera_pb2_grpc

app = FastAPI()

def get_leases():
    leases = []

    # temp: simulate localhost as another camera node
    leases.append({
        "expiry": 0,
        "mac": "00:00:00:00:00:00",
        "ip": "host.docker.internal",
        "hostname": "localhost",
        "client_id": "localhost"
    })
    try:
        with open("/var/lib/misc/dnsmasq.leases", "r") as f:
            for line in f.readlines():
                parts = line.split()
                if len(parts) >= 5:
                    leases.append({
                        "expiry": int(parts[0]),
                        "mac": parts[1],
                        "ip": parts[2],
                        "hostname": parts[3],
                        "client_id": parts[4]
                    })
    except FileNotFoundError:
        print("dnsmasq leases file not found, skipping")
    return leases

@app.get("/api")
def hello():
    return {"message": "controller is running"}

@app.get("/api/status")
def node_status():
    try:
        statuses = []
        for lease in get_leases():
            addr = f"{lease['ip']}:50051"
            node = camera_pb2_grpc.CameraNodeStub(grpc.insecure_channel(addr))
            status = node.GetStatus(camera_pb2.StatusRequest(), timeout=2)
            statuses.append({"hostname": lease["hostname"], "uptime_s": round(status.uptime_s, 1)})
    except grpc.RpcError as err:
        raise HTTPException(400)
    return {"statuses": statuses}