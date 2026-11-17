import os
from concurrent import futures
from contextlib import asynccontextmanager
import threading
from google.protobuf.json_format import MessageToDict
import grpc
from fastapi import FastAPI, HTTPException
import pose_pb2
import pose_pb2_grpc

JOINTS = ["nose", "l_eye", "r_eye", "l_ear", "r_ear",
          "l_shoulder", "r_shoulder", "l_elbow", "r_elbow",
          "l_wrist", "r_wrist", "l_hip", "r_hip",
          "l_knee", "r_knee", "l_ankle", "r_ankle"]

latest = {} # camera_id -> newest PoseFrame


class PoseReceiver(pose_pb2_grpc.PoseStreamServicer):
    def Stream(self, request_iterator, context):
        count = 0
        for frame in request_iterator:
            count += 1
            latest[frame.camera_id] = frame
            print(f"{frame.camera_id} seq={frame.seq} people={len(frame.people)}")
            # for p, person in enumerate(frame.people):
            #     print(f"  person {p}  score {person.score:.2f}")
            #     kp = list(person.keypoints)
            #     for j in range(len(kp) // 3):
            #         x, y, c = kp[3 * j : 3 * j + 3]
            #         print(f"    {j:2} {JOINTS[j]:<10}  x={x:6.1f}  y={y:6.1f}  conf={c:.2f}")
        return pose_pb2.StreamSummary(frames_received=count)


@asynccontextmanager
async def lifespan(app: FastAPI):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))  # each connected Pi holds one worker
    pose_pb2_grpc.add_PoseStreamServicer_to_server(PoseReceiver(), server)
    server.add_insecure_port("0.0.0.0:50052")
    server.start()   # runs on its own thread
    yield
    server.stop(grace=2)


app = FastAPI(lifespan=lifespan)    # link fastapi and grcp

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
    except FileNotFoundError as ex:
        print("dnsmasq leases file not found:", ex)
    print("leases are:", leases)
    return leases

@app.get("/api")
def hello():
    return {"message": "controller is running"}

@app.get("/api/leases")
def api_leases():
    return {"leases:": get_leases()}

@app.get("/api/skeleton")
def skeleton():
    frames = list(latest.values())
    return {"frames": [MessageToDict(f, preserving_proto_field_name=True) for f in frames]}