# -*- coding: utf-8 -*-
"""
用 pandas 处理你抓取的电影数据，演示 pandas 能做什么。
运行前确认 CSV 文件路径正确（数据在 素材资源 文件夹里）。
"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding="utf-8")  # 让 Windows 控制台正常显示中文

# 1. 读入 CSV（你保存时用了 utf-8-sig，所以这里也要写一样的编码）
df = pd.read_csv("../素材资源/第二次抓取电影网站数据.csv", encoding="utf-8-sig")

print("=" * 60)
print("1. 数据长什么样")
print("=" * 60)
print("形状（行数, 列数）：", df.shape)
print("列名：", list(df.columns))
print("\n前 5 行：")
print(df.head())

# 2. 数据清洗：把文本转成真正的数字
print("\n" + "=" * 60)
print("2. 清洗：年份 / 评分 / 时长 转成数字")
print("=" * 60)
df["年份"] = df["年份"].str.strip("()").astype(int)          # "(2026)" -> 2026
df["评分"] = df["评分"].astype(int)                            # "92" -> 92
# 时长 "2h 22m" -> 142 分钟
df["时长分钟"] = (df["时长"].str.extract(r"(\d+)h").fillna(0).astype(int) * 60 +
                  df["时长"].str.extract(r"(\d+)m").fillna(0).astype(int))
print(df[["电影名称", "年份", "评分", "时长", "时长分钟"]].head())

# 3. 排序：评分最高的 10 部
print("\n" + "=" * 60)
print("3. 评分 Top 10")
print("=" * 60)
top10 = df.sort_values("评分", ascending=False).head(10)
print(top10[["电影名称", "年份", "评分", "导演"]].to_string(index=False))

# 4. 统计：各语言、各导演出现次数
print("\n" + "=" * 60)
print("4. 各语言电影数量")
print("=" * 60)
print(df["语言"].value_counts())

print("\n" + "=" * 60)
print("5. 作品最多的导演 Top 5")
print("=" * 60)
print(df["导演"].value_counts().head(5))

# 6. 分组统计：每个年份的电影数量和平均评分
print("\n" + "=" * 60)
print("6. 每年电影数量与平均评分")
print("=" * 60)
print(df.groupby("年份")["评分"].agg(数量="count", 平均评分="mean").sort_values("年份"))

# 7. 筛选：只看动画电影
print("\n" + "=" * 60)
print("7. 动画电影（类型里含“动画”）")
print("=" * 60)
print(df[df["类型"].str.contains("动画")][["电影名称", "年份", "评分"]].to_string(index=False))

# 8. 简单统计值
print("\n" + "=" * 60)
print("8. 几个整体数字")
print("=" * 60)
print("电影总数：", len(df))
print("评分均值：", round(df["评分"].mean(), 1))
print("评分最高：", df["评分"].max(), "| 最低：", df["评分"].min())
print("时长均值：", round(df["时长分钟"].mean(), 0), "分钟")
