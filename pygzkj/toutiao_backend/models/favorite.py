# models/favorite.py —— 收藏表(favorite)：用户和新闻的“多对多”中间表

# 导入 datetime 类，用于时间字段的类型标注
from datetime import datetime

# 导入数据库列类型和约束：
#   UniqueConstraint 唯一约束  Index 索引  Integer 整数  ForeignKey 外键  DateTime 时间
from sqlalchemy import UniqueConstraint, Index, Integer, ForeignKey, DateTime
# 导入声明式映射三件套：DeclarativeBase 基类 / Mapped 类型注解 / mapped_column 定义列
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from models.news import News   # 导入新闻模型，是为了下面 ForeignKey(News.id) 引用新闻表的主键
from models.users import User  # 导入用户模型，是为了下面 ForeignKey(User.id) 引用用户表的主键


class Base(DeclarativeBase):
    """模型基类"""
    pass  # 空基类，只用于让 Favorite 继承


class Favorite(Base):
    """
    收藏表ORM模型：记录“哪个用户收藏了哪条新闻”
    """
    __tablename__ = 'favorite'  # 表名

    # 表级别设置
    # UniqueConstraint: 唯一约束 -> (用户,新闻) 这个组合只能出现一次，即同一用户对同一新闻只能收藏一次
    __table_args__ = (
        UniqueConstraint('user_id', 'news_id', name='user_news_unique'),  # (user_id, news_id) 联合唯一
        Index('fk_favorite_user_idx', 'user_id'),   # 给 user_id 建索引，加速按用户查
        Index('fk_favorite_news_idx', 'news_id'),   # 给 news_id 建索引，加速按新闻查
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="收藏ID")  # 主键自增
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False, comment="用户ID")  # 外键 -> 用户表，哪个用户收藏
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey(News.id), nullable=False, comment="新闻ID")  # 外键 -> 新闻表，收藏了哪条新闻
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="收藏时间")  # 收藏时间

    def __repr__(self):  # 只影响 print 打印效果，和数据库无关

        return f"<Favorite(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, created_at={self.created_at})>"  # 打印格式
