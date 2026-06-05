import math


# -----------------------------
# Soft budget penalty (same logic as rules.py)
# -----------------------------
def budget_penalty(price, budget_min, budget_max):
    if price <= budget_max:
        return 0.0

    excess = price - budget_max

    # smooth increasing penalty
    return math.log1p(excess / 1000) * 0.6


# -----------------------------
# Main recommendation engine
# -----------------------------
def recommend_laptop(df, weights, rule_context=None):

    def normalize(value, min_value, max_value):
        if max_value == min_value:
            return 0.5
        return (value - min_value) / (max_value - min_value)

    def estimate_battery_life(row):
        cpu_factor = 1 + (row["CPU_Score"] * 0.12)
        gpu_factor = 1 + (row["GPU_Score"] * 0.15)
        ram_factor = 1 + ((row["RAM_GB"] / 8) * 0.02)
        battery_life = row["Battery_Wh"] / (cpu_factor * gpu_factor * ram_factor)

        cpu_name = str(row.get("CPU", "")).upper()
        if "APPLE" in cpu_name:
            battery_life *= 1.25

        return battery_life

    def to_tier(value, min_value, max_value):
        if max_value == min_value:
            return 3
        normalized = (value - min_value) / (max_value - min_value)
        tier = int(round(normalized * 4)) + 1
        return max(1, min(5, tier))

    def price_to_tier(price, tiers):
        for index, threshold in enumerate(tiers, start=1):
            if price <= threshold:
                return index
        return len(tiers)

    cpu_min, cpu_max = df["CPU_Score"].min(), df["CPU_Score"].max()
    gpu_min, gpu_max = df["GPU_Score"].min(), df["GPU_Score"].max()
    ram_min, ram_max = df["RAM_GB"].min(), df["RAM_GB"].max()
    storage_min, storage_max = df["Storage_GB"].min(), df["Storage_GB"].max()
    battery_min, battery_max = df["Battery_Wh"].min(), df["Battery_Wh"].max()
    display_min, display_max = df["Display_Score"].min(), df["Display_Score"].max()
    price_min, price_max = df["Price_Num"].min(), df["Price_Num"].max()
    size_min, size_max = df["Display_Size"].min(), df["Display_Size"].max()

    battery_life_scores = df.apply(estimate_battery_life, axis=1)
    battery_life_min, battery_life_max = battery_life_scores.min(), battery_life_scores.max()

    rule_context = rule_context or {}

    user_processing = rule_context.get("user_processing", 1)
    user_graphics = rule_context.get("user_graphics", 1)
    user_display = rule_context.get("user_display", 1)
    user_portability = rule_context.get("user_portability", 1)
    user_storage = rule_context.get("user_storage", 1)
    user_budget_tier = rule_context.get("user_budget_tier", 3)
    performance_rank = rule_context.get("performance_rank", 4)
    cost_rank = rule_context.get("cost_rank", 4)
    portability_rank = rule_context.get("portability_rank", 4)
    user_gaming = rule_context.get("user_gaming", False)
    budget_tiers = rule_context.get("budget_tiers", [2999, 5999, 8999, 12999, 20000])
    budget_max = rule_context.get("budget_max", None)
    prefer_apple_for_portability = rule_context.get("prefer_apple_for_portability", False)

    recommendations = []

    for _, row in df.iterrows():

        # -----------------------------
        # Base scoring system
        # -----------------------------
        cpu_norm = normalize(row["CPU_Score"], cpu_min, cpu_max)
        gpu_norm = normalize(row["GPU_Score"], gpu_min, gpu_max)
        ram_norm = normalize(row["RAM_GB"], ram_min, ram_max)
        storage_norm = normalize(row["Storage_GB"], storage_min, storage_max)
        battery_life = estimate_battery_life(row)
        battery_norm = normalize(battery_life, battery_life_min, battery_life_max)
        display_norm = normalize(row["Display_Score"], display_min, display_max)
        price_norm = normalize(row["Price_Num"], price_min, price_max)
        size_norm = normalize(row["Display_Size"], size_min, size_max)

        portability_norm = 1 - size_norm
        gpu_name = str(row.get("GPU", "")).upper()
        if "RTX" in gpu_name:
            portability_norm *= 0.7

        score = (
            cpu_norm * weights["cpu"]
            + gpu_norm * weights["gpu"]
            + ram_norm * weights["ram"]
            + storage_norm * weights["storage"]
            + battery_norm * weights["battery"]
            + display_norm * weights["display"]
            + portability_norm * weights["portability"]
            - price_norm * weights["price"]
        )

        rule_score = 0.0
        conflict_score = 0.0
        conflict_warning = False

        processing_tier = to_tier(row["CPU_Score"], cpu_min, cpu_max)
        graphics_tier = to_tier(row["GPU_Score"], gpu_min, gpu_max)
        display_tier = to_tier(row["Display_Score"], display_min, display_max)
        portability_tier = to_tier(portability_norm, 0.0, 1.0)
        storage_tier = to_tier(row["Storage_GB"], storage_min, storage_max)
        price_tier = price_to_tier(row["Price_Num"], budget_tiers)

        if user_processing >= 4:
            if processing_tier == 5:
                rule_score += 5.0
            elif processing_tier == 4:
                rule_score += 3.0
            elif processing_tier <= 2:
                rule_score -= 8.0

        if user_gaming or user_graphics >= 4:
            if graphics_tier >= 4:
                rule_score += 6.0
            elif graphics_tier == 3:
                rule_score += 3.0
            elif graphics_tier == 1:
                rule_score -= 15.0

            gpu_name = str(row.get("GPU", "")).upper()
            if "RTX" not in gpu_name and graphics_tier <= 2:
                conflict_score -= 100.0
                conflict_warning = True

        if user_display >= 4:
            if display_tier == 5:
                rule_score += 4.0
            elif display_tier == 3:
                rule_score += 1.5
            elif display_tier == 1:
                rule_score -= 5.0

        if user_portability >= 4:
            if portability_tier == 5:
                rule_score += 5.0
            elif portability_tier == 4:
                rule_score += 3.0
            elif portability_tier == 1:
                rule_score -= 10.0

        if user_storage >= 4:
            if storage_tier >= user_storage:
                rule_score += 2.5
            else:
                rule_score -= 3.0

        if (user_processing >= 4 or user_graphics >= 4) and user_budget_tier <= 2:
            if cost_rank < performance_rank:
                if price_tier > user_budget_tier:
                    conflict_score -= 50.0
            else:
                allowed_budget = min(user_budget_tier + 1, len(budget_tiers))
                if price_tier == allowed_budget:
                    conflict_score += 5.0
                conflict_warning = True

        if budget_max is not None and row["Price_Num"] > budget_max:
            conflict_score -= 40.0
            conflict_warning = True

        if user_graphics >= 4 and user_portability >= 4:
            cpu_name = str(row.get("CPU", "")).upper()
            gpu_name = str(row.get("GPU", "")).upper()
            if portability_rank < performance_rank:
                if portability_tier == 1:
                    conflict_score -= 15.0
                if "APPLE" in cpu_name or "IRIS" in gpu_name or graphics_tier <= 2:
                    conflict_score += 4.0
            else:
                if graphics_tier == 5:
                    conflict_score += 6.0
                if graphics_tier <= 2:
                    conflict_score -= 20.0

        if prefer_apple_for_portability and not user_gaming:
            cpu_name = str(row.get("CPU", "")).upper()
            if "APPLE" in cpu_name:
                conflict_score += 10.0

        score += (rule_score + conflict_score) / 10.0

        # -----------------------------
        # 💡 BUDGET PENALTY (NEW FIX)
        # -----------------------------
        price_penalty = budget_penalty(
            price=row["Price_Num"],
            budget_min=weights.get("budget_min", 0),
            budget_max=weights.get("budget_max", 999999)
        )

        score -= price_penalty

        # -----------------------------
        # Store result
        # -----------------------------
        recommendations.append({
            "Brand": row["Brand"],
            "Model": row["Model"],
            "Score": round(score, 2),

            "CPU": row["CPU"],
            "RAM": row["RAM"],
            "Storage": row["Storage"],
            "GPU": row["GPU"],
            "Display": row["Display"],
            "Price": row["Price"],
            "Source": row.get("Source", "N/A"),

            "RuleScore": round(rule_score, 2),
            "ConflictScore": round(conflict_score, 2),
            "ConflictWarning": conflict_warning,

            # optional debug (VERY useful for tuning)
            "Penalty": round(price_penalty, 3)
        })

    # -----------------------------
    # Sort by final score
    # -----------------------------
    recommendations.sort(
        key=lambda x: x["Score"],
        reverse=True
    )

    return recommendations