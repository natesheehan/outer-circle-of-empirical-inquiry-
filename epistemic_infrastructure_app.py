# Epistemic–Infrastructural Diagram Editor (Streamlit + PyVis)
# -----------------------------------------------------------
# Run locally with: streamlit run epistemic_infrastructure_app.py
# This app lets you edit nodes/edges and generate an interactive HTML graph.

import json
import math
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple

import streamlit as st
from pyvis.network import Network

st.set_page_config(page_title="Empirical Inquiry", layout="wide")

# ---------------------------- Data Model ----------------------------
@dataclass
class Edge:
    source: str
    target: str
    label: str = ""

@dataclass
class DiagramConfig:
    inner_nodes: List[str]
    inner_labels: Dict[str, str]
    inner_edges: List[Edge]
    outer_nodes: List[str]
    outer_labels: Dict[str, str]
    outer_edges: List[Edge]
    cross_links: List[Tuple[str, str]]  # (outer -> inner)
    show_cross_links: bool = True
    lock_positions: bool = True
    inner_radius: int = 200
    outer_radius: int = 380
    start_angle_deg: int = 90
    physics: bool = False  # disable physics to honor positions

def default_config() -> DiagramConfig:
    inner_nodes = ["Knowledge", "Models", "Data", "Objects", "Interactions"]
    inner_labels = {
        "Knowledge": "Knowledge",
        "Models": "Models\n(representing the world)",
        "Data": "Data",
        "Objects": "Objects",
        "Interactions": "Interactions\nwith the world",
    }
    inner_edges = [
        Edge("Models","Knowledge","Interpreted as"),
        Edge("Data","Models","Ordered as"),
        Edge("Objects","Data","Processed as"),
        Edge("Interactions","Objects","Produce"),
        Edge("Knowledge","Interactions","Informs further"),
    ]
    outer_nodes = ["Concepts","Standards","Metadata","Formats","Protocols"]
    outer_labels = {
        "Concepts": "Concepts",
        "Standards": "Schema/\nStandards",
        "Metadata": "Metadata",
        "Formats": "Formats",
        "Protocols": "Protocols",
    }
    outer_edges = [
        Edge("Concepts","Standards",""),
        Edge("Standards","Metadata",""),
        Edge("Metadata","Formats",""),
        Edge("Formats","Protocols",""),
        Edge("Protocols","Concepts",""),
    ]
    cross_links = [(o,i) for o in outer_nodes for i in inner_nodes]
    return DiagramConfig(
        inner_nodes=inner_nodes,
        inner_labels=inner_labels,
        inner_edges=inner_edges,
        outer_nodes=outer_nodes,
        outer_labels=outer_labels,
        outer_edges=outer_edges,
        cross_links=cross_links
    )

def to_json(cfg: DiagramConfig) -> str:
    enc = asdict(cfg)
    enc["inner_edges"] = [asdict(e) for e in cfg.inner_edges]
    enc["outer_edges"] = [asdict(e) for e in cfg.outer_edges]
    return json.dumps(enc, indent=2)

def from_json(s: str) -> DiagramConfig:
    raw = json.loads(s)
    return DiagramConfig(
        inner_nodes=raw["inner_nodes"],
        inner_labels=raw["inner_labels"],
        inner_edges=[Edge(**e) for e in raw["inner_edges"]],
        outer_nodes=raw["outer_nodes"],
        outer_labels=raw["outer_labels"],
        outer_edges=[Edge(**e) for e in raw["outer_edges"]],
        cross_links=[tuple(x) for x in raw.get("cross_links", [])],
        show_cross_links=raw.get("show_cross_links", True),
        lock_positions=raw.get("lock_positions", True),
        inner_radius=raw.get("inner_radius", 200),
        outer_radius=raw.get("outer_radius", 380),
        start_angle_deg=raw.get("start_angle_deg", 90),
        physics=raw.get("physics", False),
    )

# ---------------------------- Helpers ----------------------------
def circle_positions(names: List[str], radius: int, clockwise=True, start_angle_deg=90):
    pos = {}
    n = len(names)
    for i,name in enumerate(names):
        ang = math.radians(start_angle_deg + (-360 if clockwise else 360) * i / n)
        x = int(radius * math.cos(ang))
        y = int(radius * math.sin(ang))
        pos[name] = (x,y)
    return pos

def build_network(cfg: DiagramConfig) -> Network:
    net = Network(height="760px", width="100%", directed=True, notebook=False, cdn_resources="in_line")
    net.toggle_physics(cfg.physics)

    # positions
    inner_pos = circle_positions(cfg.inner_nodes, cfg.inner_radius, True, cfg.start_angle_deg)
    outer_pos = circle_positions(cfg.outer_nodes, cfg.outer_radius, True, cfg.start_angle_deg)

    # outer (background)
    for n in cfg.outer_nodes:
        x,y = outer_pos[n]
        net.add_node(
            n, label=cfg.outer_labels.get(n,n), x=x, y=y, physics=not cfg.lock_positions,
            shape="box", borderWidth=1, opacity=0.35,
            font={"face":"Times New Roman", "bold": True}
        )

    # inner (foreground)
    for n in cfg.inner_nodes:
        x,y = inner_pos[n]
        net.add_node(
            n, label=cfg.inner_labels.get(n,n), x=x, y=y, physics=not cfg.lock_positions,
            shape="box", borderWidth=2,
            font={"face":"Times New Roman", "bold": True}
        )

    # --- Edges ---
    def edge_label(u, v, pool):
        for e in pool:
            if (e.source == u and e.target == v) or (e.source == v and e.target == u):
                return e.label
        return ""

    # OUTER: draw cycle edges **without arrows**
    for i, u in enumerate(cfg.outer_nodes):
        v = cfg.outer_nodes[(i + 1) % len(cfg.outer_nodes)]
        net.add_edge(u, v, label=edge_label(u, v, cfg.outer_edges), arrows="", smooth=True)

    # INNER: keep arrows
    for i, u in enumerate(cfg.inner_nodes):
        v = cfg.inner_nodes[(i - 1) % len(cfg.inner_nodes)]  # prev node
        net.add_edge(u, v, label=edge_label(u, v, cfg.inner_edges), arrows="to", smooth=True)

    if cfg.show_cross_links:
        for (o,i) in cfg.cross_links:
            if (o in cfg.outer_nodes) and (i in cfg.inner_nodes):
                net.add_edge(o, i, dashes=True, arrows="to", color="gray", smooth=True)

    return net

# ---------------------------- UI ----------------------------
st.title("The outer cycle of empirical inquiry")

st.markdown(
    """
"""
)

if "cfg" not in st.session_state:
    st.session_state.cfg = default_config()

cfg = st.session_state.cfg

with st.sidebar:
    st.header("Layout & Behaviour")
    cfg.physics = st.toggle("Enable physics", value=cfg.physics, help="Turn on to freely drag nodes (positions won't lock).")
    cfg.lock_positions = st.toggle("Lock positions to circles", value=cfg.lock_positions)
    cfg.show_cross_links = st.toggle("Show cross-links (entanglement)", value=cfg.show_cross_links)
    cfg.inner_radius = st.slider("Inner radius", 120, 320, cfg.inner_radius, step=10)
    cfg.outer_radius = st.slider("Outer radius", 300, 600, cfg.outer_radius, step=10)
    cfg.start_angle_deg = st.slider("Start angle (degrees)", 0, 360, cfg.start_angle_deg, step=10)

    st.subheader("Import / Export")
    json_in = st.text_area("Paste config JSON to import (optional)")
    if st.button("Import JSON"):
        try:
            st.session_state.cfg = from_json(json_in)
            st.success("Imported configuration.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

    st.download_button("Download current JSON", data=to_json(cfg), file_name="diagram_config.json", mime="application/json")

# Node editors
col1, col2 = st.columns(2)
with col1:
    st.subheader("Inner cycle")
    new_inner = st.text_input("Inner nodes (comma-separated, order matters)", value=", ".join(cfg.inner_nodes))
    if st.button("Update inner order/labels"):
        names = [x.strip() for x in new_inner.split(",") if x.strip()]
        if len(names) >= 3:
            # keep existing labels where possible
            labels = {n: cfg.inner_labels.get(n, n) for n in names}
            cfg.inner_nodes = names
            cfg.inner_labels = labels
            st.success("Inner order updated.")
        else:
            st.error("Please provide at least 3 inner nodes.")

    for n in cfg.inner_nodes:
        cfg.inner_labels[n] = st.text_input(f"Label for inner node '{n}'", value=cfg.inner_labels.get(n,n))

    st.markdown("**Inner edges (cycle)**")
    for i in range(len(cfg.inner_nodes)):
        u = cfg.inner_nodes[i]
        v = cfg.inner_nodes[(i+1) % len(cfg.inner_nodes)]
        # find existing edge
        label_val = ""
        for e in cfg.inner_edges:
            if e.source == u and e.target == v:
                label_val = e.label
        new_label = st.text_input(f"Label for edge {u} → {v}", value=label_val or "")
        # update or insert
        found = False
        for e in cfg.inner_edges:
            if e.source == u and e.target == v:
                e.label = new_label
                found = True
        if not found:
            cfg.inner_edges.append(Edge(u,v,new_label))

with col2:
    st.subheader("Outer cycle")
    new_outer = st.text_input("Outer nodes (comma-separated, order matters)", value=", ".join(cfg.outer_nodes))
    if st.button("Update outer order/labels"):
        names = [x.strip() for x in new_outer.split(",") if x.strip()]
        if len(names) >= 3:
            labels = {n: cfg.outer_labels.get(n, n) for n in names}
            cfg.outer_nodes = names
            cfg.outer_labels = labels
            st.success("Outer order updated.")
        else:
            st.error("Please provide at least 3 outer nodes.")

    for n in cfg.outer_nodes:
        cfg.outer_labels[n] = st.text_input(f"Label for outer node '{n}'", value=cfg.outer_labels.get(n,n))

    st.markdown("**Outer edges (cycle)**")
    for i in range(len(cfg.outer_nodes)):
        u = cfg.outer_nodes[i]
        v = cfg.outer_nodes[(i+1) % len(cfg.outer_nodes)]
        # find existing
        label_val = ""
        for e in cfg.outer_edges:
            if e.source == u and e.target == v:
                label_val = e.label
        new_label = st.text_input(f"Label for edge {u} → {v}", value=label_val or "")
        found = False
        for e in cfg.outer_edges:
            if e.source == u and e.target == v:
                e.label = new_label
                found = True
        if not found:
            cfg.outer_edges.append(Edge(u,v,new_label))

st.subheader("Cross-links (outer → inner)")
st.caption("Enter pairs like 'Concepts→Knowledge, Metadata→Data'. Leave blank to keep defaults.")
pairs_in = st.text_input("Outer→Inner pairs (comma-separated)")
if st.button("Set cross-links"):
    try:
        pairs = []
        if pairs_in.strip():
            for token in pairs_in.split(","):
                a = token.strip()
                if "→" in a:
                    o,i = [x.strip() for x in a.split("→",1)]
                elif "->" in a:
                    o,i = [x.strip() for x in a.split("->",1)]
                else:
                    continue
                pairs.append((o,i))
        else:
            pairs = [(o,i) for o in cfg.outer_nodes for i in cfg.inner_nodes]
        cfg.cross_links = pairs
        st.success("Cross-links updated.")
    except Exception as e:
        st.error(f"Failed to parse pairs: {e}")

# Build & display


net = build_network(cfg)
html = net.generate_html()

st.components.v1.html(html, height=780, scrolling=True)

# Downloads
st.download_button("Download interactive HTML", data=html, file_name="diagram.html", mime="text/html")