FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    tigervnc-standalone-server \
    tigervnc-common \
    novnc \
    websockify \
    python3 \
    python3-pip \
    usbip \
    usbutils \
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install qFlipper dependencies (headless)
RUN pip3 install pyserial

WORKDIR /app
COPY usbip_bridge.sh /app/usbip_bridge.sh
COPY novnc_proxy.py /app/novnc_proxy.py
RUN chmod +x /app/usbip_bridge.sh

# VNC display config
ENV DISPLAY=:1
ENV VNC_PORT=5901
ENV NOVNC_PORT=6080
ENV VNC_GEOMETRY=1280x800

EXPOSE 5901 6080

CMD ["bash", "-c", "\
    Xtigervnc :1 -rfbport=${VNC_PORT} -SecurityTypes=None -localhost -geometry=${VNC_GEOMETRY} -depth=24 & \
    sleep 2 && \
    DISPLAY=:1 startxfce4 & \
    websockify --web=/usr/share/novnc ${NOVNC_PORT} localhost:${VNC_PORT} \
"]
