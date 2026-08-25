# -*- coding: utf-8 -*-
"""
用 matplotlib 画电影类型分布柱状图。
类型字段是"动画，动作，冒险"这种多个值用中文逗号分隔的，先拆开再统计。
"""
import matplotlib
matplotlib.use("Agg")  # 不弹窗，直接把图存成文件
import matplotlib.pyplot as plt
import pandas as pd

# 中文显示
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 读数据，把"类型"按中文逗号拆开、展开成一行一个，再计数
df = pd.read_csv("../素材资源/第二次抓取电影网站数据.csv", encoding="utf-8-sig")
types = df["类型"].str.split("，").explode().value_counts()

# 画图：单一系列，只用一种颜色
fig, ax = plt.subplots(figsize=(10, 5), dpi=110)
color = "#2a78d6"
bars = ax.bar(types.index, types.values, color=color, width=0.6)

# 每根柱子顶端标出数量
for b in bars:
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3,
            str(int(b.get_height())), ha="center", va="bottom",
            fontsize=9, color="#0b0b0b")

# 标题、坐标轴、网格（弱化的网格线）
ax.set_title("电影类型分布", fontsize=14, color="#0b0b0b", pad=14)
ax.set_ylabel("电影数量", color="#52514e")
ax.set_xlabel("类型", color="#52514e")
ax.tick_params(axis="x", labelrotation=45, colors="#52514e")
ax.tick_params(axis="y", colors="#898781")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#c3c2b7")
ax.spines["bottom"].set_color("#c3c2b7")
ax.yaxis.grid(True, color="#e1e0d9", linewidth=1)
ax.set_axisbelow(True)
ax.set_ylim(0, types.max() + 4)

plt.tight_layout()
plt.savefig("电影类型柱状图.png")
print(types.to_string())          # 顺便把数字打印出来
print("\n图片已保存到：电影类型柱状图.png")
