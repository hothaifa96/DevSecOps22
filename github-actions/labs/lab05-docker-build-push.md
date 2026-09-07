# Lab 05: Docker Build and Push

## Overview

In this lab, you will build Docker images within GitHub Actions, tag them with meaningful identifiers, and push them to both Docker Hub and GitHub Container Registry (GHCR). Containerized deployments are a cornerstone of modern DevSecOps pipelines.

---

## Objectives

By the end of this lab, you will be able to:

- Write a production-quality Dockerfile with multi-stage builds
- Build Docker images in GitHub Actions
- Tag images with commit SHA, branch name, and semantic versions
- Push images to Docker Hub
- Push images to GitHub Container Registry (GHCR)
- Use Docker layer caching to speed up builds
- Scan Docker images for vulnerabilities before pushing

---

## Prerequisites

- Completed **Lab 02** (Node.js project with tests)
- A Docker Hub account ([hub.docker.com](https://hub.docker.com))
- Basic understanding of Docker and Dockerfiles
- Docker installed locally for testing (optional but recommended)

---

## Step-by-Step Instructions

### Step 1: Create the Application

Ensure your `github-actions-labs` repo has the calculator app from Lab 02. Additionally, create a simple Express API. Install Express:

```bash
npm install express
```

Create `src/server.js`:

```javascript
const express = require("express");
const { add, subtract, multiply, divide } = require("./calculator");

const app = express();
app.use(express.json());

app.get("/health", (req, res) => {
  res.json({ status: "healthy", timestamp: new Date().toISOString() });
});

app.post("/calculate", (req, res) => {
  const { operation, a, b } = req.body;
  try {
    let result;
    switch (operation) {
      case "add":
        result = add(a, b);
        break;
      case "subtract":
        result = subtract(a, b);
        break;
      case "multiply":
        result = multiply(a, b);
        break;
      case "divide":
        result = divide(a, b);
        break;
      default:
        return res.status(400).json({ error: "Invalid operation" });
    }
    res.json({ operation, a, b, result });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 3000;
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

module.exports = app;
```

### Step 2: Create a Multi-Stage Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
# ============================================
# Stage 1: Dependencies
# ============================================
FROM node:20-alpine AS dependencies

WORKDIR /app

# Copy package files for dependency caching
COPY package.json package-lock.json ./

# Install production dependencies only
RUN npm ci --only=production

# ============================================
# Stage 2: Test (used in CI only)
# ============================================
FROM node:20-alpine AS test

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm test

# ============================================
# Stage 3: Production
# ============================================
FROM node:20-alpine AS production

# Add labels for container metadata
LABEL org.opencontainers.image.source="https://github.com/OWNER/github-actions-labs"
LABEL org.opencontainers.image.description="DevSecOps Calculator API"
LABEL org.opencontainers.image.version="1.0.0"

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

WORKDIR /app

# Copy production dependencies from Stage 1
COPY --from=dependencies /app/node_modules ./node_modules

# Copy application code
COPY src/ ./src/
COPY package.json ./

# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start the application
CMD ["node", "src/server.js"]
```

### Step 3: Create a .dockerignore File

Create `.dockerignore`:

```
node_modules
coverage
test-results
.git
.github
.gitignore
*.md
.eslintrc.json
jest.config.js
tests/
```

### Step 4: Test the Docker Build Locally (Optional)

```bash
docker build -t calculator-api:local .
docker run -p 3000:3000 calculator-api:local

# In another terminal:
curl http://localhost:3000/health
curl -X POST http://localhost:3000/calculate \
  -H "Content-Type: application/json" \
  -d '{"operation":"add","a":5,"b":3}'
```

### Step 5: Configure Docker Hub Credentials

1. Go to [Docker Hub](https://hub.docker.com) and create an account (if you don't have one).
2. Go to **Account Settings** > **Security** > **New Access Token**.
3. Create a token named `github-actions` with **Read & Write** permissions.
4. Copy the token.
5. In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**.
6. Create the following secrets:

| Secret Name | Value |
|-------------|-------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | The access token you just created |

### Step 6: Create the Docker Build and Push Workflow

Create `.github/workflows/docker-build-push.yml`:

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]
    tags: ["v*.*.*"]
  pull_request:
    branches: [main]

env:
  DOCKERHUB_IMAGE: ${{ secrets.DOCKERHUB_USERNAME }}/calculator-api
  GHCR_IMAGE: ghcr.io/${{ github.repository_owner }}/calculator-api

jobs:
  build-and-push:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest

    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Generate Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ env.DOCKERHUB_IMAGE }}
            ${{ env.GHCR_IMAGE }}
          tags: |
            # Tag with branch name
            type=ref,event=branch
            # Tag with PR number
            type=ref,event=pr
            # Tag with semantic version (from git tags)
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            # Tag with commit SHA
            type=sha,prefix=
            # Tag as 'latest' for default branch
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Login to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Login to GitHub Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          target: production
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_DATE=${{ github.event.head_commit.timestamp }}
            VCS_REF=${{ github.sha }}

      - name: Display image details
        run: |
          echo "## Docker Image Details" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### Tags" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          echo "${{ steps.meta.outputs.tags }}" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### Labels" >> $GITHUB_STEP_SUMMARY
          echo '```json' >> $GITHUB_STEP_SUMMARY
          echo "${{ steps.meta.outputs.labels }}" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY

  scan-image:
    name: Scan Docker Image
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.event_name != 'pull_request'

    permissions:
      contents: read
      packages: read
      security-events: write

    steps:
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/${{ github.repository_owner }}/calculator-api:latest
          format: "table"
          exit-code: "0"
          ignore-unfixed: true
          vuln-type: "os,library"
          severity: "CRITICAL,HIGH"
          output: "trivy-results.txt"

      - name: Display scan results
        if: always()
        run: |
          echo "## Container Vulnerability Scan" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          cat trivy-results.txt >> $GITHUB_STEP_SUMMARY || echo "No results file found" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY

      - name: Upload scan results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: trivy-scan-results
          path: trivy-results.txt
```

### Step 7: Commit and Push

```bash
git add -A
git commit -m "Add Docker build and push workflow"
git push origin main
```

### Step 8: Verify the Build

1. Go to the **Actions** tab and watch the workflow run.
2. Verify the image builds successfully.
3. Check Docker Hub for the pushed image at `https://hub.docker.com/r/<username>/calculator-api`.
4. Check GHCR at `https://github.com/<username>/github-actions-labs/pkgs/container/calculator-api`.

### Step 9: Test Semantic Version Tagging

Create and push a Git tag to trigger a versioned release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Go to the **Actions** tab and observe that the image is tagged with:
- `1.0.0`
- `1.0`
- `1`
- The commit SHA
- `latest`

### Step 10: Verify GHCR Package Visibility

1. Go to your GitHub profile > **Packages**.
2. Find the `calculator-api` package.
3. Click on it to see all tags and versions.
4. Optionally change the visibility to **Public**.

---

## Expected Outcomes

After completing this lab, you should see:

1. A multi-stage Dockerfile that builds an optimized production image.
2. A Docker image pushed to both Docker Hub and GitHub Container Registry.
3. Multiple tags on the image: branch name, commit SHA, semantic versions, and `latest`.
4. Docker layer caching via GitHub Actions cache reducing subsequent build times.
5. A Trivy vulnerability scan running against the pushed image.
6. Images built but not pushed for pull request events.

---

## Bonus Challenges

1. **Add multi-platform builds** for AMD64 and ARM64:
   ```yaml
   - name: Set up QEMU
     uses: docker/setup-qemu-action@v3

   - name: Build and push (multi-platform)
     uses: docker/build-push-action@v5
     with:
       platforms: linux/amd64,linux/arm64
       push: true
       tags: ${{ steps.meta.outputs.tags }}
   ```

2. **Add a container structure test** using Google's container-structure-test to verify the image contents, ports, and metadata.

3. **Set up automated Docker Hub description sync** using `peter-evans/dockerhub-description@v4` to keep the Docker Hub README in sync with your repository.

4. **Implement a build matrix** that builds both `node:20-alpine` and `node:20-slim` base image variants.

5. **Add image signing** using Cosign to cryptographically sign your container images:
   ```yaml
   - name: Sign the image
     uses: sigstore/cosign-installer@v3
   - run: cosign sign --yes ghcr.io/${{ github.repository_owner }}/calculator-api:latest
   ```

---

## Key Concepts Learned

- **Multi-Stage Builds**: Separate build, test, and production stages to minimize final image size
- **Docker Buildx**: Extended build capabilities including caching and multi-platform support
- **Docker Metadata Action**: Automatically generates tags and labels based on Git events
- **GitHub Container Registry (GHCR)**: GitHub's built-in container registry at `ghcr.io`
- **Layer Caching**: Using `cache-from` and `cache-to` with GitHub Actions cache to speed up builds
- **Image Scanning**: Running vulnerability scanners (Trivy) against built images
- **Non-Root User**: Running containers as a non-root user for improved security
- **HEALTHCHECK**: Docker-native health monitoring for containerized applications
