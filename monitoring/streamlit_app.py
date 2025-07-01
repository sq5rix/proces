#!/usr/bin/env python3
"""
Kafka IoT Simulator - Streamlit Monitoring Dashboard
Real-time monitoring of Kafka cluster and IoT edge devices
"""

import json
import logging
import os
import queue
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from kafka import KafkaAdminClient, KafkaConsumer
from kafka.admin import ConfigResource, ConfigResourceType
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.WARNING)

# Page configuration
st.set_page_config(
    page_title="Kafka IoT Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .device-online {
        color: #28a745;
        font-weight: bold;
    }
    .device-offline {
        color: #dc3545;
        font-weight: bold;
    }
    .device-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)


class KafkaMonitor:
    def __init__(self, bootstrap_servers: str = "kafka:29092"):  # Fixed port
        self.bootstrap_servers = bootstrap_servers
        self.message_queue = queue.Queue(maxsize=1000)
        self.consumer_thread = None
        self.running = False
        self.device_data = {}
        self.kafka_health = {"status": "unknown", "last_check": None}

    def start_consumer(self):
        """Start Kafka consumer in a separate thread"""
        if self.consumer_thread is None or not self.consumer_thread.is_alive():
            self.running = True
            self.consumer_thread = threading.Thread(
                target=self._consume_messages, daemon=True
            )
            self.consumer_thread.start()

    def stop_consumer(self):
        """Stop Kafka consumer"""
        self.running = False
        if self.consumer_thread:
            self.consumer_thread.join(timeout=1)

    def _consume_messages(self):
        """Consume messages from Kafka in background thread"""
        try:
            consumer = KafkaConsumer(
                "iot-sensors",
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                consumer_timeout_ms=1000,
                auto_offset_reset="latest",
            )

            while self.running:
                try:
                    messages = consumer.poll(timeout_ms=1000)
                    for topic_partition, records in messages.items():
                        for record in records:
                            if not self.message_queue.full():
                                self.message_queue.put(
                                    {"timestamp": datetime.now(), "data": record.value}
                                )
                            else:
                                # Remove oldest message if queue is full
                                try:
                                    self.message_queue.get_nowait()
                                    self.message_queue.put(
                                        {
                                            "timestamp": datetime.now(),
                                            "data": record.value,
                                        }
                                    )
                                except queue.Empty:
                                    pass
                except Exception as e:
                    if self.running:
                        st.error(f"Error consuming messages: {e}")
                        time.sleep(1)  # Add a small sleep to prevent busy-waiting

        except Exception as e:
            if self.running:
                st.error(f"Failed to connect to Kafka: {e}")

    def get_recent_messages(self, count: int = 100) -> List[Dict]:
        """Get recent messages from the queue"""
        messages = []

        # Extract all messages from queue
        while not self.message_queue.empty():
            try:
                messages.append(self.message_queue.get_nowait())
            except queue.Empty:
                break

        # Take the most recent messages
        recent_messages = messages[-count:] if len(messages) > count else messages

        # Put messages back in queue
        for msg in recent_messages:
            if not self.message_queue.full():
                self.message_queue.put(msg)

        return recent_messages

    def update_device_data(self, messages: List[Dict]):
        """Update device data from messages"""
        for msg in messages:
            device_id = msg["data"]["device_id"]
            sensor_type = msg["data"]["sensor_type"]

            if device_id not in self.device_data:
                self.device_data[device_id] = {
                    "sensor_type": sensor_type,
                    "last_seen": msg["timestamp"],
                    "message_count": 0,
                    "data_history": [],
                }

            self.device_data[device_id]["last_seen"] = msg["timestamp"]
            self.device_data[device_id]["message_count"] += 1
            self.device_data[device_id]["data_history"].append(
                {"timestamp": msg["timestamp"], "data": msg["data"]["data"]}
            )

            # Keep only last 100 data points
            if len(self.device_data[device_id]["data_history"]) > 100:
                self.device_data[device_id]["data_history"] = self.device_data[
                    device_id
                ]["data_history"][-100:]

    def check_kafka_health(self) -> Dict[str, Any]:
        """Check Kafka cluster health"""
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            metadata = admin_client.describe_cluster()

            self.kafka_health = {
                "status": "healthy",
                "last_check": datetime.now(),
                "brokers": len(metadata.brokers) if hasattr(metadata, "brokers") else 1,
                "cluster_id": getattr(metadata, "cluster_id", "unknown"),
            }
        except Exception as e:
            self.kafka_health = {
                "status": "unhealthy",
                "last_check": datetime.now(),
                "error": str(e),
            }

        return self.kafka_health


# Initialize monitor
if "kafka_monitor" not in st.session_state:
    # Use environment variable for Kafka servers
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    st.session_state.kafka_monitor = KafkaMonitor(kafka_servers)
    st.session_state.kafka_monitor.start_consumer()

monitor = st.session_state.kafka_monitor

# Sidebar
st.sidebar.title("🚀 Kafka IoT Monitor")
st.sidebar.markdown("---")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto Refresh (5s)", value=False)

# Manual refresh button
if st.sidebar.button("🔄 Refresh Now"):
    st.rerun()

# Kafka connection settings
st.sidebar.subheader("⚙️ Settings")
kafka_servers = st.sidebar.text_input(
    "Kafka Bootstrap Servers",
    value=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
    help="Comma-separated list of Kafka bootstrap servers",
)

if st.sidebar.button("Reconnect to Kafka"):
    st.session_state.kafka_monitor.stop_consumer()
    st.session_state.kafka_monitor = KafkaMonitor(kafka_servers)
    st.session_state.kafka_monitor.start_consumer()
    st.success("Reconnected to Kafka!")

# Main content
st.title("📊 Kafka IoT Simulator Dashboard")
st.markdown("Real-time monitoring of Kafka cluster and IoT edge devices")

# Get recent messages and update device data
recent_messages = monitor.get_recent_messages(100)
monitor.update_device_data(recent_messages)

# Check Kafka health
kafka_health = monitor.check_kafka_health()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Overview", "🔧 Device Details", "📡 Kafka Health", "📊 Historical Data"]
)

with tab1:
    st.header("System Overview")

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Active Devices", value=len(monitor.device_data), delta=None)

    with col2:
        total_messages = sum(
            device["message_count"] for device in monitor.device_data.values()
        )
        st.metric(
            label="Total Messages",
            value=f"{total_messages:,}",
            delta=len(recent_messages) if recent_messages else 0,
        )

    with col3:
        online_devices = sum(
            1
            for device in monitor.device_data.values()
            if (datetime.now() - device["last_seen"]).seconds < 30
        )
        st.metric(label="Online Devices", value=online_devices, delta=None)

    with col4:
        status_color = "🟢" if kafka_health["status"] == "healthy" else "🔴"
        st.metric(
            label="Kafka Status",
            value=f"{status_color} {kafka_health['status'].title()}",
            delta=None,
        )

    st.markdown("---")

    # Device status table
    st.subheader("Device Status")

    if monitor.device_data:
        device_status_data = []
        for device_id, device_info in monitor.device_data.items():
            last_seen_seconds = (datetime.now() - device_info["last_seen"]).seconds

            if last_seen_seconds < 30:
                status = "🟢 Online"
            elif last_seen_seconds < 60:
                status = "🟡 Warning"
            else:
                status = "🔴 Offline"

            device_status_data.append(
                {
                    "Device ID": device_id,
                    "Type": device_info["sensor_type"].title(),
                    "Status": status,
                    "Last Seen": device_info["last_seen"].strftime("%H:%M:%S"),
                    "Messages": device_info["message_count"],
                    "Last Seen (seconds ago)": last_seen_seconds,
                }
            )

        df_status = pd.DataFrame(device_status_data)
        st.dataframe(df_status, use_container_width=True)
    else:
        st.info("No device data available. Make sure the IoT simulators are running.")

    # Real-time message feed
    st.subheader("Recent Messages")

    if recent_messages:
        # Show last 5 messages
        for msg in recent_messages[-5:]:
            with st.expander(
                f"📨 {msg['data']['device_id']} - {msg['timestamp'].strftime('%H:%M:%S')}"
            ):
                st.json(msg["data"])
    else:
        st.info("No recent messages. Check Kafka connection.")

with tab2:
    st.header("Device Details")

    if monitor.device_data:
        # Device selector
        selected_device = st.selectbox(
            "Select Device",
            options=list(monitor.device_data.keys()),
            key="device_selector",
        )

        if selected_device:
            device_info = monitor.device_data[selected_device]

            col1, col2 = st.columns(2)

            with col1:
                st.subheader(f"📱 {selected_device}")
                st.write(f"**Type:** {device_info['sensor_type'].title()}")
                st.write(
                    f"**Last Seen:** {device_info['last_seen'].strftime('%Y-%m-%d %H:%M:%S')}"
                )
                st.write(f"**Total Messages:** {device_info['message_count']:,}")

            with col2:
                # Device-specific chart
                if device_info["data_history"]:
                    df_device = pd.DataFrame(
                        [
                            {
                                "timestamp": item["timestamp"],
                                "value": (
                                    item["data"].get("temperature_celsius", 0)
                                    if device_info["sensor_type"] == "temperature"
                                    else (
                                        item["data"].get("humidity_percentage", 0)
                                        if device_info["sensor_type"] == "humidity"
                                        else (
                                            1
                                            if item["data"].get(
                                                "motion_detected", False
                                            )
                                            else 0
                                        )
                                    )
                                ),
                            }
                            for item in device_info["data_history"][-20:]
                        ]
                    )

                    if device_info["sensor_type"] == "motion":
                        fig = px.scatter(
                            df_device,
                            x="timestamp",
                            y="value",
                            title=f"{selected_device} Motion Detection",
                        )
                    else:
                        fig = px.line(
                            df_device,
                            x="timestamp",
                            y="value",
                            title=f"{selected_device} Readings",
                        )

                    st.plotly_chart(fig, use_container_width=True)

            # Recent data table
            st.subheader("Recent Data")
            if device_info["data_history"]:
                recent_data = []
                for item in device_info["data_history"][-10:]:
                    recent_data.append(
                        {
                            "Timestamp": item["timestamp"].strftime("%H:%M:%S"),
                            "Data": json.dumps(item["data"], indent=2),
                        }
                    )

                df_recent = pd.DataFrame(recent_data)
                st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No device data available.")

with tab3:
    st.header("Kafka Cluster Health")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Connection Status")
        if kafka_health["status"] == "healthy":
            st.success(f"✅ Kafka cluster is healthy")
            st.write(f"**Brokers:** {kafka_health.get('brokers', 'Unknown')}")
            st.write(f"**Cluster ID:** {kafka_health.get('cluster_id', 'Unknown')}")
        else:
            st.error(f"❌ Kafka cluster is unhealthy")
            if "error" in kafka_health:
                st.error(f"Error: {kafka_health['error']}")

        if kafka_health["last_check"]:
            st.write(
                f"**Last Check:** {kafka_health['last_check'].strftime('%Y-%m-%d %H:%M:%S')}"
            )

    with col2:
        st.subheader("Connection Settings")
        st.code(f"Bootstrap Servers: {monitor.bootstrap_servers}")
        st.code("Topic: iot-sensors")

        # Connection test button
        if st.button("Test Connection"):
            with st.spinner("Testing connection..."):
                health = monitor.check_kafka_health()
                if health["status"] == "healthy":
                    st.success("Connection successful!")
                else:
                    st.error("Connection failed!")

    # Topic information
    st.subheader("📋 Topic Information")
    st.info("Topic: iot-sensors (Main IoT data topic)")

with tab4:
    st.header("Historical Analytics")

    if monitor.device_data:
        # Time range selector
        time_range = st.selectbox(
            "Select Time Range",
            options=["Last 15 minutes", "Last 30 minutes", "Last 1 hour", "All time"],
            index=1,
        )

        # Filter data based on time range
        now = datetime.now()
        if time_range == "Last 15 minutes":
            cutoff_time = now - timedelta(minutes=15)
        elif time_range == "Last 30 minutes":
            cutoff_time = now - timedelta(minutes=30)
        elif time_range == "Last 1 hour":
            cutoff_time = now - timedelta(hours=1)
        else:
            cutoff_time = datetime.min

        # Combined sensor data chart
        st.subheader("📊 All Sensors Overview")

        # Prepare data for combined chart
        all_data = []
        for device_id, device_info in monitor.device_data.items():
            for item in device_info["data_history"]:
                if item["timestamp"] >= cutoff_time:
                    row = {
                        "device_id": device_id,
                        "sensor_type": device_info["sensor_type"],
                        "timestamp": item["timestamp"],
                    }

                    if device_info["sensor_type"] == "temperature":
                        row["value"] = item["data"].get("temperature_celsius", 0)
                        row["unit"] = "°C"
                    elif device_info["sensor_type"] == "humidity":
                        row["value"] = item["data"].get("humidity_percentage", 0)
                        row["unit"] = "%"
                    elif device_info["sensor_type"] == "motion":
                        row["value"] = (
                            1 if item["data"].get("motion_detected", False) else 0
                        )
                        row["unit"] = "detected"

                    all_data.append(row)

        if all_data:
            df = pd.DataFrame(all_data)

            # Create subplots for different sensor types
            sensor_types = df["sensor_type"].unique()

            if len(sensor_types) > 1:
                fig = make_subplots(
                    rows=len(sensor_types),
                    cols=1,
                    subplot_titles=[
                        f"{stype.title()} Sensors" for stype in sensor_types
                    ],
                    shared_xaxes=True,
                )

                for i, sensor_type in enumerate(sensor_types, 1):
                    sensor_data = df[df["sensor_type"] == sensor_type]

                    for device_id in sensor_data["device_id"].unique():
                        device_data = sensor_data[sensor_data["device_id"] == device_id]

                        if sensor_type == "motion":
                            fig.add_trace(
                                go.Scatter(
                                    x=device_data["timestamp"],
                                    y=device_data["value"],
                                    mode="markers",
                                    name=device_id,
                                    showlegend=(i == 1),
                                ),
                                row=i,
                                col=1,
                            )
                        else:
                            fig.add_trace(
                                go.Scatter(
                                    x=device_data["timestamp"],
                                    y=device_data["value"],
                                    mode="lines+markers",
                                    name=device_id,
                                    showlegend=(i == 1),
                                ),
                                row=i,
                                col=1,
                            )

                fig.update_layout(
                    height=200 * len(sensor_types), title="Historical Sensor Data"
                )
                st.plotly_chart(fig, use_container_width=True)

            # Statistics table
            st.subheader("📈 Summary Statistics")

            stats_data = []
            for sensor_type in sensor_types:
                sensor_data = df[df["sensor_type"] == sensor_type]

                if sensor_type != "motion":
                    stats_data.append(
                        {
                            "Sensor Type": sensor_type.title(),
                            "Min Value": f"{sensor_data['value'].min():.2f}",
                            "Max Value": f"{sensor_data['value'].max():.2f}",
                            "Average": f"{sensor_data['value'].mean():.2f}",
                            "Data Points": len(sensor_data),
                        }
                    )
                else:
                    motion_count = sensor_data["value"].sum()
                    stats_data.append(
                        {
                            "Sensor Type": sensor_type.title(),
                            "Min Value": "N/A",
                            "Max Value": "N/A",
                            "Average": f"{motion_count} detections",
                            "Data Points": len(sensor_data),
                        }
                    )

            if stats_data:
                df_stats = pd.DataFrame(stats_data)
                st.dataframe(df_stats, use_container_width=True)
        else:
            st.info(f"No data available for the selected time range: {time_range}")
    else:
        st.info(
            "No historical data available. Make sure the IoT simulators are running."
        )

# Footer
st.markdown("---")
st.markdown(
    "🚀 **Kafka IoT Simulator Dashboard** | "
    "Built with Streamlit & Plotly | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

# Auto-refresh mechanism
if auto_refresh:
    # Use st.experimental_rerun() to trigger a rerun for auto-refresh
 st.experimental_rerun()
