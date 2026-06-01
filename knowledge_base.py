import pandas as pd
CPU_SCORES = {
    "Intel N100": 2,

    "i7-1355U": 7,
    "i7-1360P": 8,
    "i7-13700H": 9,
    "i7-13700HX": 10,
    "i9-13900HX": 10,

    "Intel i5-14450HX": 9,

    "Intel Ultra 9 386H": 10,

    "Apple A18 Pro": 6,
    "Apple M5": 9,
    "Apple M5 Pro": 10
}

GPU_SCORES = {
    "Intel UHD": 2,
    "Iris Xe": 4,

    "RTX 4060": 8,
    "RTX 4070": 9,
    "RTX 4080": 10,

    "RTX 5060": 9,
    "RTX 5070 Ti": 10,

    "-": 3
}


def parse_ram(ram):
    return int(ram.replace("GB", ""))


def parse_storage(storage):

    storage = storage.upper()

    if "TB" in storage:
        return float(storage.replace("TB", "").replace("SSD", "").strip()) * 1024

    return float(storage.replace("GB", "").replace("SSD", "").strip())


def parse_battery(battery):
    return float(battery.replace("Wh", ""))


def parse_price(price):

    return float(
        price.replace("RM", "")
        .replace(",", "")
    )


def parse_display(display):
    display_upper = display.upper()

    size = None
    for token in display_upper.split("\""):
        token = token.strip()
        if token and token.replace(".", "", 1).isdigit():
            size = float(token)
            break

    width = None
    height = None
    if "X" in display_upper:
        parts = display_upper.split("X")
        left = "".join(ch for ch in parts[0] if ch.isdigit())
        right = "".join(ch for ch in parts[1] if ch.isdigit())
        if left.isdigit() and right.isdigit():
            width = int(left)
            height = int(right)

    megapixels = 0.0
    if width and height:
        megapixels = (width * height) / 1_000_000

    panel_bonus = 0.0
    if "OLED" in display_upper or "XDR" in display_upper:
        panel_bonus = 0.2

    size_bonus = 0.0
    if size:
        size_bonus = min(size / 20.0, 1.0) * 0.1

    return megapixels + panel_bonus + size_bonus


def parse_display_size(display):
    display_upper = display.upper()
    for token in display_upper.split("\""):
        token = token.strip()
        if token and token.replace(".", "", 1).isdigit():
            return float(token)
    return 0.0


def load_laptops():
    df = pd.read_csv("laptops.csv")


    df["RAM_GB"] = df["RAM"].apply(parse_ram)

    df["Storage_GB"] = df["Storage"].apply(parse_storage)

    df["Battery_Wh"] = df["Battery"].apply(parse_battery)

    df["Price_Num"] = df["Price"].apply(parse_price)

    df["CPU_Score"] = df["CPU"].map(CPU_SCORES)

    df["GPU_Score"] = df["GPU"].map(GPU_SCORES)

    df["Display_Score"] = df["Display"].apply(parse_display)

    df["Display_Size"] = df["Display"].apply(parse_display_size)

    return df