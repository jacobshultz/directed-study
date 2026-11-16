import argparse
import sys
import time

import numpy as np

from picamera2 import CompletedRequest, MappedArray, Picamera2
from picamera2.devices.imx500 import IMX500, NetworkIntrinsics
from picamera2.devices.imx500.postprocess import COCODrawer
from picamera2.devices.imx500.postprocess_highernet import postprocess_higherhrnet

import socket

import grpc
import pose_pb2
import pose_pb2_grpc



last_boxes = None
last_scores = None
last_keypoints = None
WINDOW_SIZE_H_W = (480, 640)

JOINTS = ["nose", "l_eye", "r_eye", "l_ear", "r_ear",
          "l_shoulder", "r_shoulder", "l_elbow", "r_elbow",
          "l_wrist", "r_wrist", "l_hip", "r_hip",
          "l_knee", "r_knee", "l_ankle", "r_ankle"]

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", type=str, help="Path of the model", default="/usr/share/imx500-models/imx500_network_higherhrnet_coco.rpk"
    )
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--detection-threshold", type=float, default=0.3, help="Post-process detection threshold")
    parser.add_argument("--labels", type=str, help="Path to the labels file")
    parser.add_argument("--print-intrinsics", action="store_true", help="Print JSON network_intrinsics then exit")
    return parser.parse_args()


def get_drawer():
    categories = intrinsics.labels
    categories = [c for c in categories if c and c != "-"]
    return COCODrawer(categories, imx500, needs_rescale_coords=False)


if __name__ == "__main__":
    args = get_args()

    # This must be called before instantiation of Picamera2
    imx500 = IMX500(args.model)
    intrinsics = imx500.network_intrinsics
    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "pose estimation"
    elif intrinsics.task != "pose estimation":
        print("Network is not a pose estimation task", file=sys.stderr)
        exit()

    # Override intrinsics from args
    for key, value in vars(args).items():
        if key == 'labels' and value is not None:
            with open(value, 'r') as f:
                intrinsics.labels = f.read().splitlines()
        elif hasattr(intrinsics, key) and value is not None:
            setattr(intrinsics, key, value)

    # Defaults
    if intrinsics.inference_rate is None:
        intrinsics.inference_rate = 10
    if intrinsics.labels is None:
        with open("assets/coco_labels.txt", "r") as f:
            intrinsics.labels = f.read().splitlines()
    intrinsics.update_with_defaults()

    if args.print_intrinsics:
        print(intrinsics)
        exit()

    drawer = get_drawer()

    picam2 = Picamera2(imx500.camera_num)   # thread that recieves frames
    config = picam2.create_preview_configuration(controls={'FrameRate': intrinsics.inference_rate}, buffer_count=12)

    imx500.show_network_fw_progress_bar()
    picam2.start(config, show_preview=False) # thread that can do output, processing, UI
    imx500.set_auto_aspect_ratio()
    
    def frames():
        seq = 0
        while True:
            md = picam2.capture_metadata()
            np_outputs = imx500.get_outputs(metadata=md, add_batch=True)
            if np_outputs is None:
                continue
            keypoints, scores, boxes = postprocess_higherhrnet(
                outputs=np_outputs,
                img_size=WINDOW_SIZE_H_W,
                img_w_pad=(0, 0),
                img_h_pad=(0, 0),
                detection_threshold=args.detection_threshold,
                network_postprocess=True,
            )

            ts = md["SensorTimestamp"]
            msg = pose_pb2.PoseFrame(
                camera_id=socket.gethostname(),
                seq=seq,
                sensor_timestamp_ns=ts,
                capture_time_unix_ns=time.time_ns() - (time.monotonic_ns() - ts),  # sensor clock -> unix time
                width=WINDOW_SIZE_H_W[1],
                height=WINDOW_SIZE_H_W[0],
            )
            if scores is not None and len(scores) > 0:
                kps = np.reshape(np.stack(keypoints, axis=0), (len(scores), 17, 3))
                for person, score in zip(kps, scores):
                    msg.people.add(keypoints=person.flatten().tolist(), score=float(score))

            seq += 1
            yield msg


    channel = grpc.insecure_channel("192.168.2.5:50051")    # connect to the control server
    stub = pose_pb2_grpc.PoseStreamStub(channel)
    summary = stub.Stream(frames())   # gRPC pulls each yielded frame and sends it
    print("server received", summary.frames_received, "frames")   # only reached if frames() ends
