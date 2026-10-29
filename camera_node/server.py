import time
from concurrent import futures

import grpc

import camera_pb2
import camera_pb2_grpc

START = time.monotonic()


class CameraNode(camera_pb2_grpc.CameraNodeServicer):
    def GetStatus(self, request, context):
        print("GetStatus called from", context.peer())
        return camera_pb2.NodeStatus(node_id="laptop", uptime_s=time.monotonic() - START)


server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
camera_pb2_grpc.add_CameraNodeServicer_to_server(CameraNode(), server)
server.add_insecure_port("0.0.0.0:50051")
server.start()
print("gRPC server listening on port 50051")
server.wait_for_termination()