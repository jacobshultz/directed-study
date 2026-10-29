# Docker Setup

This document details the containerization setup.

## Control Node
Containers:
- Postgres
- Semaphore UI
- Deno (built from Dockerfile.Deno)
- Nginx (build from Dockerfile.Nginx)

Building custom images for the deno and nginx are required to ensure the config files / web server files are included.