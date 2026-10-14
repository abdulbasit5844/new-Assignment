# Lab-06: Containerized Build Stage Automation

| | |
|---|---|
| Student | Abdul Basit |
| Registration number | FA22-BAI-001 |
| Roll number | FA22-BAI-001 |

A Flask REST API serving a linear regression model, packaged with Docker, run with Docker Compose,
and started by a Jenkins Declarative Pipeline triggered by a GitHub push webhook.

## Live API

Deployed on EC2 by the Jenkins Build stage:

- http://13.51.196.90:5000/health
- http://13.51.196.90:5000/predict?x1=2&x2=3&x3=1

## Model

```
y = a1*x1 + a2*x2 + a3*x3 + b
```

Coefficients are generated once at startup with `random.seed(22001)` (the numeric form of
FA22-BAI-001), in this order:

```python
a1 = random.uniform(-5, 5)    # -3.984510644599022
a2 = random.uniform(-5, 5)    #  4.56271882220536
a3 = random.uniform(-5, 5)    #  3.70577478687175
b  = random.uniform(-10, 10)  # -3.165726219936655
```

## Project files

| File | Purpose |
|---|---|
| `app.py` | Flask API (`/predict`, `/health`) |
| `requirements.txt` | Flask and gunicorn |
| `Dockerfile` | Python 3.12 slim image, served by gunicorn on `0.0.0.0:5000` |
| `docker-compose.yml` | Runs the Docker Hub image on host port 5000, `restart: "no"` |
| `Jenkinsfile` | Declarative pipeline: Checkout and Build (compose pull + up) |

## API

### `GET /health`

```json
{"status": "ok"}
```

### `GET /predict?x1=2&x2=3&x3=1`

```json
{"registration number": "FA22-BAI-001", "prediction": 6.26}
```

If `x1`, `x2` or `x3` is missing, not a number, or not finite (`nan`, `inf`), the API returns
**HTTP 400**:

```json
{"registration number": "FA22-BAI-001", "error": "invalid input",
 "details": ["missing required parameter 'x3'"]}
```

## 1. Test the API locally

### Without Docker

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

In a second terminal:

```bash
curl http://localhost:5000/health
curl "http://localhost:5000/predict?x1=2&x2=3&x3=1"   # prediction 6.26
curl -i "http://localhost:5000/predict?x1=2&x2=3"     # HTTP 400
curl -i "http://localhost:5000/predict?x1=a&x2=3&x3=1" # HTTP 400
```

### With Docker

```bash
docker build -t linear-regression-lab06:local .
docker run --rm -p 5000:5000 linear-regression-lab06:local
```

Then run the same `curl` commands.

## 2. Build and push the Docker image to Docker Hub

Docker Hub repository: https://hub.docker.com/r/aen8aen/linear-regression-lab06

```bash
docker login
docker build -t aen8aen/linear-regression-lab06:latest .
docker push aen8aen/linear-regression-lab06:latest
```

The Jenkins pipeline does not build or push images; it only pulls the image you pushed here.

## 3. Push the code to GitHub

Create an empty repository on GitHub, then:

```bash
git init
git add .
git commit -m "Lab-06: containerized build stage automation"
git branch -M main
git remote add origin https://github.com/abdulbasit5844/new-Assignment.git
git push -u origin main
```

## 4. Prepare the EC2 / Jenkins host

On the machine running Jenkins (for example your EC2 instance):

1. Install Docker and the Docker Compose v2 plugin (`docker compose version` must work), plus `curl`.
2. Let the Jenkins user run Docker: `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins`.
3. Open inbound port **5000** in the EC2 security group, and the Jenkins port **8081** (Jenkins runs on 8081 here because 8080 is used by another container).
4. Do **not** start the API manually. It stays DOWN until Jenkins runs the Build stage.
   `docker-compose.yml` uses `restart: "no"` and nothing is enabled on boot, so after a reboot
   the API is DOWN again until the next Jenkins build.

Check that it is down before the first build:

```bash
curl http://13.51.196.90:5000/health   # should fail: connection refused
```

## 5. Configure Jenkins

1. Install the plugins **Git**, **GitHub**, and **Pipeline**.
2. Create a **Pipeline** job:
   - *Definition*: **Pipeline script from SCM**
   - *SCM*: Git, *Repository URL*: `https://github.com/abdulbasit5844/new-Assignment.git`, *Branch*: `*/main`
   - *Script Path*: `Jenkinsfile`
   - *Build Triggers*: tick **GitHub hook trigger for GITScm polling**
3. The image is set in the `Jenkinsfile` (`DOCKER_IMAGE = aen8aen/linear-regression-lab06:latest`).
   To use a different image, set a `DOCKER_IMAGE` environment variable in
   *Manage Jenkins → System → Global properties*; it overrides the default.

## 6. Configure the GitHub webhook

In the GitHub repository: *Settings → Webhooks → Add webhook*

- *Payload URL*: `http://13.51.196.90:8081/github-webhook/` (the trailing slash is required)
- *Content type*: `application/json`
- *Events*: **Just the push event**

GitHub must be able to reach Jenkins, so the Jenkins port must be open to GitHub.

## 7. Deploy through Jenkins

Push a commit (or click *Build Now* once, which also registers the `githubPush()` trigger).
The pipeline:

1. **Checkout**: `checkout scm` fetches the repository configured in the job.
2. **Build**: runs `docker compose pull` and `docker compose up -d --force-recreate`, then polls
   `/health` for up to 60 seconds and calls `/predict?x1=2&x2=3&x3=1`.
   The script uses `set -eu`, so any failing command or an API that never
   becomes healthy fails the build.

Verify from your own machine:

```bash
curl http://13.51.196.90:5000/health
curl "http://13.51.196.90:5000/predict?x1=2&x2=3&x3=1"
```

To stop the API manually:

```bash
DOCKER_IMAGE=aen8aen/linear-regression-lab06:latest docker compose down
```
