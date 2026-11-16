GRPC is a Remote Procedure Call framework. 

Generate files from proto in shell:

`python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. grpc_shared/scd.proto`