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
def recommend_laptop(df, weights):

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