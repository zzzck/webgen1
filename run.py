from core.manager import Manager
import os
import json

# 在os中设置OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = "sk-Fukj5EU0DA0wGBHMNfhEX5IgggeuieNfKf1ExfYpDC7ELkL1"
os.makedirs("output", exist_ok=True)

brief = """
我想要设计一个宣传网页，使用html+css+js实现。以下是产品信息。其余内容包括风格、色彩等要求我均可接受，无须询问。

产品：新疆葵花籽 500g，小包装；19.9 元。
主题：春节 × 团圆 × 嗑瓜子 × 年味。
"""

manager = Manager()
html = manager.run(brief)
with open("output/messages.json", "w", encoding="utf-8") as log_file:
    json.dump(manager.bus.dump(), log_file, ensure_ascii=False, indent=2)

with open("output/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("网页已生成：output/index.html")
