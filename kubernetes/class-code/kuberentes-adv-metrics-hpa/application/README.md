# Flask HPA Demo

This is a small Flask app for demonstrating the Kubernetes Horizontal Pod Autoscaler.

## Files

- `app.py` — Flask application. Background thread does CPU work proportional to `load_level`.
  - `GET /` — health check
  - `GET /up/<n>` — add `n` to the pod's CPU load level
  - `GET /down/<n>` — subtract `n` from the pod's CPU load level
  - `GET /status` — current load level
- `load.sh` — bash script that sends repeated `/up/1` requests to slowly ramp CPU
- `Dockerfile` — container image
- `requirements.txt` — Python dependencies

## Build

```bash
docker build -t flask-hpa:latest .
```

## Kubernetes expectation

You are writing the Deployment, Service and HPA. Use this contract:

- **Image:** `flask-hpa:latest` (or push to a registry)
- **Port:** `5000`
- **Resources:** a small CPU request/limit, e.g. `cpu: 100m`
- **HPA target:** e.g. `averageUtilization: 50`
- **Labels:** use `app: flask-hpa` (matches the default URL in `load.sh`)

## Run the load

```bash
# default: 3 requests every 5 seconds, 60 steps = 5 minutes
./load.sh

# or customize
./load.sh http://flask-hpa:5000/up/1 5 3 40
```

## Watch

```bash
kubectl top pods -l app=flask-hpa
kubectl get hpa -w
```

## Tuning CPU ramp

If the ramp is too fast or too slow, change `BURN_MULTIPLIER` in the Deployment env:

- larger value = more CPU per load level (ramp becomes steeper)
- smaller value = less CPU per load level (ramp becomes gentler)
