FROM python:3.11-slim

# Install system dependencies: Fail2Ban, iptables, iproute2, bash, procps
RUN apt-get update && \
    apt-get install -y --no-install-recommends fail2ban iptables iproute2 bash procps && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY jail.local /etc/fail2ban/jail.local
COPY filter-http-flood.conf /etc/fail2ban/filter.d/http-flood.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY app ./app

EXPOSE 8001
ENTRYPOINT ["/entrypoint.sh"]
