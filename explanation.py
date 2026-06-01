def create_explanation(laptop, reasons):

    text = f"""
Recommended Laptop:
{laptop['Brand']} {laptop['Model']}

Specifications:
CPU: {laptop['CPU']}
RAM: {laptop['RAM']}
Storage: {laptop['Storage']}
GPU: {laptop['GPU']}
Price: {laptop['Price']}

Reasons:
"""

    for r in reasons:
        text += f"\n• {r}"

    return text