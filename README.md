
# DevOps Kubernetes Test – Web App + PostgreSQL 

This repository contains a small Flask-based web service and a PostgreSQL database
running inside a local Kubernetes cluster created with **kind**.

The goal is:

- build a minimal container image for the web service (non-root user, small base image),
- run it together with PostgreSQL in a local Kubernetes cluster,
- configure everything via ConfigMap/Secret (no hardcoded DB config),
- expose the web service from the host machine.

---

## 1. Project structure

```text
app/                         # web application source code + Dockerfile
  Dockerfile                 # docker image for the web-application
  app.py                     # flask http web-server
  requirements.txt           # requirements for the app to work

k8s/                         # manifest files .yaml
  namespace.yaml             # namespace for all resources (devops-test)
  configmap.yaml             # DB host/name/port (non-sensitive config)
  secret.yaml                # DB user/password (sensitive config)
  kind-config.yaml           # kind cluster config file` 
  
  web/
    deploy.yaml              # deployment for the web application
    nodeport-service.yaml    # nodePort Service for the web application

  postgres/
    postgresql.yaml          # StatefulSet for PostgreSQL
    postgres-service.yaml    # ClusterIP Service for PostgreSQL

    
README.md
```

## 2. Application overview

The web service exposes three endpoints:

    GET /health
    Returns {"status": "ok"} and is used for basic liveness and readiness probes to the web service Deployment 

    GET /time
    Returns the current server time in JSON.

    GET /db-check
    Tries to connect to PostgreSQL using the environment variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD and returns a JSON
    indicating whether the DB is reachable.

The service listens on port 8000 inside the container and runs as a non-root user.

## 3. Prerequisites
    - Docker
    - kind
    - kubectl

## 4. Build and load the application image
### 1) Clone or download repository
```
git clone https://github.com/purgatoriumlautus/practical_devops_test.git\
```
### 2) Build the application image from the repository root
```
cd practical_devops_test
```
```
docker build -t myapp:last ./app
```

### 3) Create the kind cluster (2 nodes: 1 control-plane, 1 worker) from k8s directory

```
cd k8s/
```
```
kind create cluster --config kind-config.yaml
```

### 4) Make the local image available inside the kind cluster:
```
kind load docker-image myapp:latest --name grune-erde-cluster
```

kind load copies the locally built myapp:last image into the node’s container runtime, so Kubernetes can pull it without using an external registry.
## 5. Configuration (ConfigMap + Secret)

All DB-related configuration is provided via Kubernetes resources instead of hardcoding.
### 5.1 Namespace

Create the namespace used by all resources:
```
kubectl apply -f namespace.yaml
```
This creates the devops-test namespace.
### 5.2 ConfigMap and Secret

Apply configuration and credentials:
```
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
```

Expected keys:

    k8s/configmap.yaml (ConfigMap db-config): #non-sensitive
        DB_HOST
        DB_PORT
        DB_NAME

    k8s/secret.yaml (Secret db-secret): #sensitive
        DB_USER
        DB_PASSWORD

The web application Deployment and Postgres StatefulSet reads these values via env.valueFrom.configMapKeyRef
and env.valueFrom.secretKeyRef.
## 6. Deploy PostgreSQL

Deploy the PostgreSQL instance and its Service:
```
kubectl apply -f postgres/postgresql.yaml
kubectl apply -f postgres/postgres-service.yaml
```

The StatefulSet uses the  postgres:16-alpine image

The postgres-service.yaml exposes the database as a ClusterIP Service

    PostgreSQL reads its configuration from the same ConfigMap/Secret:
        
        POSTGRES_USER ← DB_USER
        POSTGRES_PASSWORD ← DB_PASSWORD
        POSTGRES_DB ← DB_NAME



You can verify that the Pod is running:
```
kubectl get pods -n devops-test
kubectl describe svc postgresql -n devops-test
```

## 7. Deploy the web application

Deploy the web service and its Service:
```
kubectl apply -f web/deploy.yaml
kubectl apply -f web/nodeport-service.yaml
```
Key points in deploy.yaml:

    image: myapp:last

    Environment variables:
        DB_HOST
        DB_PORT
        DB_NAME
        DB_USER
        DB_PASSWORD

Probes are made on /health endpoint every 10 seconds with initial delay of 5 sec:


nodeport-service.yaml exposes the application as a NodePort Service
(e.g. nodePort: 8000).
## 8. Accessing the application

Check the Service:
```
kubectl get svc -n devops-test
```
Expected output:

    NAME            TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
    grune-nodeport  NodePort   10.96.123.45   <none>        8000:30000/TCP   ...
    postgresql      ClusterIP  None           <none>        5432/TCP         ...


 you can usually reach the NodePort on the host via web-browser or curl:

    http://localhost:8000/health
    http://localhost:8000/time
    http://localhost:8000/db-check


## 9. Verifying everything

### Check Pods

Expected: one Pod for the web app, one for PostgreSQL, both in Running state.

```
kubectl get pods -n devops-test
```

### Check health/time endpoints:
Expected: json containing {"status":"ok"} and json containing {"time":"2025-..."}

    curl http://localhost:8000/health
    curl http://localhost:8000/time

---

### Verify DB connectivity endpoint:
Expected: json containing {"db":"ok"}

```
curl http://localhost:8000/db-check
```
### Verify container logs accesibility
Expected:
HTTP request logs (method + path).

Example: 
`10.244.1.1 - - [10/Dec/2025 01:02:06] "GET /health HTTP/1.1" 200 -`
```
kubectl logs -n devops-test deployment/grune-app-deployment
```


## 10. Cleanup

To delete all resources:
```
kubectl delete namespace devops-test
```
To delete the kind cluster:
```
kind delete cluster --name grune-erde-cluster
```