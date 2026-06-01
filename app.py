import streamlit as st

from knowledge_base import load_laptops
from rules import apply_rules
from inference_engine import recommend_laptop
from explanation import create_explanation


st.title("Student-Centric Laptop Expert System")

# ----------------------------
# FEATURES LIST (RANKING)
# ----------------------------
FEATURES = ["Performance", "Storage", "Battery", "Cost"]

if "selected_features" not in st.session_state:
    st.session_state.selected_features = []


def toggle_feature(feature):
    """Handles click order ranking logic"""
    if feature in st.session_state.selected_features:
        st.session_state.selected_features.remove(feature)
    else:
        st.session_state.selected_features.append(feature)


def get_rank(feature):
    """Return rank number if selected"""
    if feature in st.session_state.selected_features:
        return st.session_state.selected_features.index(feature) + 1
    return None


# ----------------------------
# RANKING UI
# ----------------------------
st.subheader("Rank Your Priorities (Click in order)")

for feature in FEATURES:
    rank = get_rank(feature)

    label = feature
    if rank:
        label = f"{feature} (Rank {rank})"

    st.checkbox(
        label,
        value=(feature in st.session_state.selected_features),
        key=f"cb_{feature}",
        on_change=toggle_feature,
        args=(feature,)
    )

# ----------------------------
# LIKERT SCALE
# ----------------------------
st.subheader("Importance Ratings")

cpu_importance = st.slider("CPU Importance", 1, 5, 3)
gpu_importance = st.slider("GPU Importance", 1, 5, 3)
ram_importance = st.slider("RAM Importance", 1, 5, 3)

battery_importance = st.slider("Battery Importance", 1, 5, 3)
storage_importance = st.slider("Storage Importance", 1, 5, 3)
display_importance = st.slider("Display Importance", 1, 5, 3)

gaming = st.checkbox("I play games")
content_creation = st.checkbox("I do content creation")
travel = st.checkbox("I travel often")

# ----------------------------
# BUDGET CATEGORY
# ----------------------------
st.subheader("Budget Category")

budget = st.radio(
    "Select your budget range",
    [
        "Very Low (RM 1,000 - RM 2,999)",
        "Low (RM 3,000 - RM 5,999)",
        "Medium (RM 6,000 - RM 8,999)",
        "High (RM 9,000 - RM 12,999)",
        "Premium (RM 13,000+)"
    ]
)

# ----------------------------
# RECOMMEND BUTTON
# ----------------------------
if st.button("Recommend"):

    # convert ranking list → dictionary
    rank_map = {f: i + 1 for i, f in enumerate(st.session_state.selected_features)}

    profile = {
        "performance_rank": rank_map.get("Performance", 4),
        "storage_rank": rank_map.get("Storage", 4),
        "battery_rank": rank_map.get("Battery", 4),
        "cost_rank": rank_map.get("Cost", 4),

        "cpu_importance": cpu_importance,
        "gpu_importance": gpu_importance,
        "ram_importance": ram_importance,
        "battery_importance": battery_importance,
        "storage_importance": storage_importance,
        "display_importance": display_importance,

        "gaming": gaming,
        "content_creation": content_creation,
        "travel": travel,

        "budget_category": budget
    }

    laptops = load_laptops()

    weights, reasons = apply_rules(profile)

    results = recommend_laptop(laptops, weights)

    best = results[0]

    st.success(f"{best['Brand']} {best['Model']}")

    st.metric("Score", best["Score"])

    st.write(create_explanation(best, reasons))

    st.subheader("Top 5 Recommendations")

    st.dataframe(results[:5])