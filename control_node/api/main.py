import os

import grpc
from fastapi import FastAPI, HTTPException

import camera_pb2
import camera_pb2_grpc

NODE_ADDRESS = os.environ.get("NODE_ADDRESS", "host.docker.internal:50051")

app = FastAPI()
node = camera_pb2_grpc.CameraNodeStub(grpc.insecure_channel(NODE_ADDRESS))


@app.get("/api")
def hello():
    return {"message": "controller is running"}


@app.get("/api/status")
def node_status():
    try:
        status = node.GetStatus(camera_pb2.StatusRequest(), timeout=2)
    except grpc.RpcError as err:
        raise HTTPException(503, f"Could not reach {NODE_ADDRESS}: {err.code().name}")
    return {"node_id": status.node_id, "uptime_s": round(status.uptime_s, 1)}