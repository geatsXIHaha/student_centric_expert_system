import math

# -----------------------------
# Budget categories (soft ranges)
# -----------------------------
BUDGET_MAP = {
    "Very Low (RM 1,000 - RM 2,999)": (1000, 2999),
    "Low (RM 3,000 - RM 5,999)": (3000, 5999),
    "Medium (RM 6,000 - RM 8,999)": (6000, 8999),
    "High (RM 9,000 - RM 12,999)": (9000, 12999),
    "Premium (RM 13,000+)": (13000, 20000),
    "Low": (0, 3000),
    "Medium": (3000, 6000),
    "Upper-Mid": (6000, 9000),
    "High": (9000, 12000),
    "Premium": (12000, 20000)
}

BUDGET_TIERS = [2999, 5999, 8999, 12999, 20000]


# -----------------------------
# Soft budget penalty function
# (non-linear: farther = harsher)
# -----------------------------
def budget_penalty(price, budget_min, budget_max):
    if price <= budget_max:
        return 0.0

    excess = price - budget_max

    # smooth exponential-like penalty
    return math.log1p(excess / 1000) * 0.6


# -----------------------------
# Main rule engine
# -----------------------------
def apply_rules(profile):

    weights = {
        "cpu": 0.0,
        "gpu": 0.0,
        "ram": 0.0,
        "storage": 0.0,
        "battery": 0.0,
        "display": 0.0,
        "portability": 0.0,
        "price": 0.0
    }

    reasons = []

    # ranking weight system (user preference ordering)
    rank_weight = {
        1: 0.40,
        2: 0.30,
        3: 0.20,
        4: 0.10,
        5: 0.05
    }

    # -----------------------------
    # Core ranking preferences
    # -----------------------------
    performance_weight = rank_weight.get(profile["performance_rank"], 0)
    weights["cpu"] += performance_weight * 0.5
    weights["gpu"] += performance_weight * 0.35
    weights["ram"] += performance_weight * 0.15
    weights["storage"] += rank_weight.get(profile["storage_rank"], 0)
    weights["battery"] += rank_weight.get(profile["battery_rank"], 0)
    weights["portability"] += rank_weight.get(profile.get("portability_rank", 4), 0)

    # cost sensitivity (higher rank = more cost concern)
    weights["price"] += rank_weight.get(profile["cost_rank"], 0)

    # -----------------------------
    # Slider importance (1-5)
    # -----------------------------
    importance_scale = 0.08

    weights["cpu"] += (profile.get("cpu_importance", 1) - 1) * importance_scale
    weights["gpu"] += (profile.get("gpu_importance", 1) - 1) * importance_scale
    weights["ram"] += (profile.get("ram_importance", 1) - 1) * importance_scale
    weights["battery"] += (profile.get("battery_importance", 1) - 1) * importance_scale
    weights["storage"] += (profile.get("storage_importance", 1) - 1) * importance_scale
    weights["display"] += (profile.get("display_importance", 1) - 1) * importance_scale
    weights["portability"] += (profile.get("portability_importance", 1) - 1) * importance_scale

    # -----------------------------
    # Optional preferences
    # -----------------------------
    if profile.get("gaming"):
        weights["gpu"] += 0.8
        weights["cpu"] += 0.2
        reasons.append("Gaming selected → GPU and CPU prioritized.")

    if profile.get("content_creation"):
        weights["cpu"] += 0.4
        weights["gpu"] += 0.3
        weights["ram"] += 0.3
        weights["display"] += 0.3
        weights["storage"] += 0.2
        reasons.append("Content creation selected → CPU, GPU, RAM, display prioritized.")

    if profile.get("travel"):
        weights["battery"] += 0.4
        weights["price"] += 0.1
        weights["portability"] += 0.35
        reasons.append("Travel selected → battery prioritized and cost sensitivity increased.")

    if profile.get("battery_importance", 0) >= 4:
        weights["battery"] += 0.4
        reasons.append("Battery life is highly important.")

    if profile.get("battery_rank") == 1:
        weights["portability"] += 0.25
        reasons.append("Battery ranked #1 → portability favored over heavy gaming rigs.")

    if profile.get("storage_importance", 0) >= 4:
        weights["storage"] += 0.4
        reasons.append("Storage capacity is highly important.")

    if profile.get("display_importance", 0) >= 4:
        weights["display"] += 0.3
        reasons.append("Display quality is highly important.")

    if profile.get("portability_importance", 0) >= 4:
        weights["portability"] += 0.3
        reasons.append("Portability is highly important.")

    prefer_apple_for_portability = (
        not profile.get("gaming")
        and (
            profile.get("travel")
            or profile.get("battery_rank") == 1
            or profile.get("portability_importance", 0) >= 4
        )
    )
    if prefer_apple_for_portability:
        reasons.append("Non-gaming portability profile → Apple efficiency favored.")

    # -----------------------------
    # Budget handling (IMPORTANT)
    # -----------------------------
    budget_label = profile.get("budget_category", "Medium")

    budget_min, budget_max = BUDGET_MAP.get(
        budget_label,
        (3000, 6000)
    )

    # store for inference engine
    weights["budget_min"] = budget_min
    weights["budget_max"] = budget_max

    reasons.append(
        f"Budget set to {budget_label} (RM {budget_min} - RM {budget_max}). "
        "Soft penalty applied for exceeding range."
    )

    total_weight = sum(
        max(value, 0.0)
        for key, value in weights.items()
        if key not in {"budget_min", "budget_max"}
    )
    if total_weight > 0:
        for key in ["cpu", "gpu", "ram", "storage", "battery", "display", "portability", "price"]:
            weights[key] = max(weights[key], 0.0) / total_weight

    budget_tier = 3
    for index, threshold in enumerate(BUDGET_TIERS, start=1):
        if budget_max <= threshold:
            budget_tier = index
            break

    rule_context = {
        "user_processing": profile.get("cpu_importance", 1),
        "user_graphics": profile.get("gpu_importance", 1),
        "user_display": profile.get("display_importance", 1),
        "user_portability": profile.get("portability_importance", 1),
        "user_storage": profile.get("storage_importance", 1),
        "user_budget_tier": budget_tier,
        "performance_rank": profile.get("performance_rank", 4),
        "cost_rank": profile.get("cost_rank", 4),
        "portability_rank": profile.get("portability_rank", 4),
        "user_gaming": profile.get("gaming", False),
        "user_travel": profile.get("travel", False),
        "prefer_apple_for_portability": prefer_apple_for_portability,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "budget_tiers": BUDGET_TIERS
    }

    return weights, reasons, rule_context