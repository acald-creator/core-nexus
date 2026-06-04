FROM docker.io/kalilinux/kali-rolling:latest

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    wget \
    nmap \
    python3 \
    python3-pip \
    python3-scapy \
    tcpdump \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add non-root user for default unprivileged execution profile
RUN useradd -m -u 1000 kali

USER kali
WORKDIR /home/kali

CMD ["sleep", "infinity"]
