"""Streamlit BI dashboard.

Run:  streamlit run dashboard/app.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from bkk_cctv.config import load_config

st.set_page_config(page_title="Bangkok CCTV Traffic", layout="wide")
st.title("Bangkok CCTV Traffic Dashboard")

cfg = load_config()
data_path = cfg["paths"]["processed"] / "traffic_features.parquet"
if not data_path.exists():
    st.warning("Run the pipeline first: python -m bkk_cctv.pipeline.flow")
    st.stop()

df = pd.read_parquet(data_path)
cameras = st.sidebar.multiselect("Camera", sorted(df["camera_id"].unique()))
if cameras:
    df = df[df["camera_id"].isin(cameras)]

c1, c2, c3 = st.columns(3)
c1.metric("Images", f"{len(df):,}")
c2.metric("Cameras", df["camera_id"].nunique())
c3.metric("Avg vehicles / image", f"{df['total'].mean():.1f}")

hourly = df.groupby("hour", as_index=False)["total"].mean()
fig = px.line(hourly, x="hour", y="total", title="Average vehicles by hour")
st.plotly_chart(fig, width="stretch")

# TODO: map of cameras (pydeck / folium), weather vs traffic, weekday heatmap
