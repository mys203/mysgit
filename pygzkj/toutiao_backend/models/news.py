# models/news.py —— 新闻相关表：分类表(news_category)、新闻表(news)

# 导入数据库列类型和约束：
#   DateTime 时间  Integer 整数  String 字符串  Index 索引  Text 长文本  ForeignKey 外键
from sqlalchemy import DateTime, Integer, String, Index, Text, ForeignKey
# 导入 datetime 类，用于时间字段的类型标注
from datetime import datetime
# 导入声明式映射三件套：DeclarativeBase 基类 / mapped_column 定义列 / Mapped 类型注解
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

# 导入 Optional，表示字段可空（可以是 None）
from typing import Optional


# 根据数据库创建模型对应的类（基类）
class Base(DeclarativeBase):
    """基类：把 created_at/updated_at 写在 Base 上，
    继承它的 Category、News 都会自动带上这两个字段"""
    # created_at 创建时间（公共字段）
    created_at : Mapped[datetime] = mapped_column(
        DateTime,             # 时间类型
        default=datetime.now, # 不带括号！插入时动态算当前时间
        comment="创建时间"
    )
    # updated_at 更新时间（公共字段）
    updated_at : Mapped[datetime] = mapped_column(
        DateTime,             # 时间类型
        default=datetime.now, # 插入时默认当前时间
        onupdate = datetime.now,  # 更新时自动刷新为当前时间
        comment="更新时间"
    )

# 第一轮表对应的模型类
class Category(Base):
    """新闻分类表"""
    __tablename__ = "news_category"  # 表名
    id :Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,comment="分类ID")  # 主键自增
    name :Mapped[str] = mapped_column(String(50),unique=True,nullable=False,comment="分类名称")  # 分类名，唯一且非空
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")  # 排序值，默认0
    def __repr__(self):  # 打印友好，与数据库无关
        return f"<Category(id={self.id}, name={self.name},sort_order={self.sort_order} )>"


# 第二轮设置模型类
class News(Base):
    """新闻表"""
    __tablename__ = "news"  # 表名

    # 表级别设置：给分类id、发布时间建索引，按这两列查询时更快
    __table_args__ = (
        Index('fk_news_category_idx', 'category_id'),   # 给 category_id 建索引
        Index('idx_publish_time', 'publish_time')       # 给 publish_time 建索引
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")  # 主键自增
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="新闻标题")  # 标题，非空
    description: Mapped[Optional[str]] = mapped_column(String(500), comment="新闻简介")  # 简介，Optional 表示可空
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="新闻内容")  # 正文，Text 长文本，非空
    image: Mapped[Optional[str]] = mapped_column(String(255), comment="封面图片URL")  # 封面图，可空
    author: Mapped[Optional[str]] = mapped_column(String(50), comment="作者")  # 作者，可空
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('news_category.id'), nullable=False)  # 外键指向分类表 id
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="浏览量")  # 浏览量，默认0
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发布时间")  # 发布时间

    def __repr__(self):  # 打印友好
        return f"<News(id={self.id},totle={self.title},views={self.views})>"
