import streamlit as st

from knowledge_base import load_laptops
from rules import apply_rules
from inference_engine import recommend_laptop
from explanation import create_explanation
from llm_explainer import generate_llm_explanation


st.title("Student-Centric Laptop Expert System")

# ----------------------------
# FEATURES LIST (RANKING)
# ----------------------------
FEATURES = ["Performance", "Storage", "Battery", "Portability", "Cost"]

if "selected_features" not in st.session_state:
    st.session_state.selected_features = []

if "llm_explanations" not in st.session_state:
    st.session_state.llm_explanations = {}

if "last_results" not in st.session_state:
    st.session_state.last_results = None

if "last_profile" not in st.session_state:
    st.session_state.last_profile = None

if "last_reasons" not in st.session_state:
    st.session_state.last_reasons = None

if "llm_status" not in st.session_state:
    st.session_state.llm_status = {}

if "best_summary" not in st.session_state:
    st.session_state.best_summary = None


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
portability_importance = st.slider("Portability Importance", 1, 5, 3)

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

    if not st.session_state.selected_features:
        st.warning("Please select at least one ranked priority before recommending.")
        st.stop()

    # convert ranking list → dictionary
    rank_map = {f: i + 1 for i, f in enumerate(st.session_state.selected_features)}

    profile = {
        "performance_rank": rank_map.get("Performance", 4),
        "storage_rank": rank_map.get("Storage", 4),
        "battery_rank": rank_map.get("Battery", 4),
        "portability_rank": rank_map.get("Portability", 4),
        "cost_rank": rank_map.get("Cost", 4),
        "selected_ranks": st.session_state.selected_features,

        "cpu_importance": cpu_importance,
        "gpu_importance": gpu_importance,
        "ram_importance": ram_importance,
        "battery_importance": battery_importance,
        "storage_importance": storage_importance,
        "display_importance": display_importance,
        "portability_importance": portability_importance,

        "gaming": gaming,
        "content_creation": content_creation,
        "travel": travel,

        "budget_category": budget
    }

    laptops = load_laptops()

    weights, reasons, rule_context = apply_rules(profile)

    results = recommend_laptop(laptops, weights, rule_context)

    st.session_state.last_results = results
    st.session_state.last_profile = profile
    st.session_state.last_reasons = reasons

    best = results[0]

    st.session_state.best_summary = {
        "brand": best["Brand"],
        "model": best["Model"],
        "score": best["Score"],
        "explanation": create_explanation(best, reasons)
    }

    best_key = f"{best['Brand']} {best['Model']}"
    st.session_state.llm_status[best_key] = "Triggering LLM..."
    with st.spinner("Generating explanation..."):
        best_llm_text = generate_llm_explanation(profile, best, reasons)
    st.session_state.llm_explanations[best_key] = best_llm_text
    st.session_state.llm_status[best_key] = "LLM response received."

    if best_key in st.session_state.llm_explanations:
        st.session_state.best_summary["llm"] = st.session_state.llm_explanations[best_key]
    elif best_key in st.session_state.llm_status:
        st.session_state.best_summary["llm"] = st.session_state.llm_status[best_key]

if st.session_state.best_summary:
    st.success(
        f"{st.session_state.best_summary['brand']} "
        f"{st.session_state.best_summary['model']}"
    )
    st.metric("Score", st.session_state.best_summary["score"])
    st.write(st.session_state.best_summary["explanation"])
    if "llm" in st.session_state.best_summary:
        st.write(st.session_state.best_summary["llm"])

st.subheader("Top 5 Recommendations")

display_results = st.session_state.last_results
display_profile = st.session_state.last_profile
display_reasons = st.session_state.last_reasons

if display_results:
    for index, laptop in enumerate(display_results[:5], start=1):
        header = f"{index}. {laptop['Brand']} {laptop['Model']} (Score {laptop['Score']})"
        explainer_key = f"{laptop['Brand']} {laptop['Model']}"
        with st.expander(header, expanded=False):
            st.write(
                "Specifications: "
                f"CPU: {laptop['CPU']}, "
                f"RAM: {laptop['RAM']}, "
                f"Storage: {laptop['Storage']}, "
                f"GPU: {laptop['GPU']}, "
                f"Display: {laptop['Display']}, "
                f"Price: {laptop['Price']}"
            )

            if st.button("View Explanation", key=f"explain_{index}"):
                st.session_state.llm_status[explainer_key] = "Triggering LLM..."
                placeholder = st.empty()
                placeholder.info("Generating response... loading")
                llm_text = generate_llm_explanation(display_profile, laptop, display_reasons)
                st.session_state.llm_explanations[explainer_key] = llm_text
                st.session_state.llm_status[explainer_key] = "LLM response received."
                placeholder.empty()

            if explainer_key in st.session_state.llm_explanations:
                st.write(st.session_state.llm_explanations[explainer_key])
            elif explainer_key in st.session_state.llm_status:
                st.info(st.session_state.llm_status[explainer_key])
else:
    st.info("Run a recommendation to see the top 5 results.")