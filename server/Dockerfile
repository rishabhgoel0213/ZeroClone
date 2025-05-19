###############################################################################
# ZeroClone – server container
# - CUDA 12.1 + cuDNN 8 runtime (Ubuntu 22.04)
# - Creates an isolated venv under /opt/venv
# - Runs the project-level setup.sh (marks it executable first)
# - Pre-loads github.com host key so git pulls don’t block
# - Exposes port 8000 for the FastAPI service
###############################################################################

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# ---- OS packages -----------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip python3-dev \
        build-essential git openssh-client wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ---- SSH known-hosts (for github.com) ---------------------------------------
RUN mkdir -p /root/.ssh && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

# ---- Copy project into the image -------------------------------------------
# NOTE: build from repo-root            ─►  docker build -f server/Dockerfile .
# The context (“.”) is the repo; this grabs everything, not just /server
WORKDIR /workspace/ZeroClone
COPY . /workspace/ZeroClone

# ---- Create and activate virtual-env; run project bootstrap -----------------
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    chmod +x ./setup.sh && \
    /bin/bash -c "source /opt/venv/bin/activate && ./setup.sh"

# Make venv the default python / pip
ENV PATH="/opt/venv/bin:${PATH}"

# ---- Expose the FastAPI port (change if your app uses a different one) ------
EXPOSE 8000

# ---- Default launch command --------------------------------------------------
# Replace `server.main:app` with your actual FastAPI entry-point.
# CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
