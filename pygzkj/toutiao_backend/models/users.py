from datetime import datetime
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column

from sqlalchemy import Index, Column, Integer, String, DateTime, Enum


class Base(DeclarativeBase):
    pass

class User(Base):

    __tablename__ = 'user'
#创建索引，意思就是下面这些东西是常访问的东西，创建之后就可以让数据库不用查全表，而是指定查询，一定内降低了服务器的压力，加快了速度
    __table_args__ = (
        Index('idx_user', 'username'),
        Index('idx_user_email', 'phone'),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="用户ID"
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="用户名"
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码（加密存储）"
    )
    nickname: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="昵称"
    )
    avatar: Mapped[Optional[str]] = mapped_column(
        String(255),
        default="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
        comment="头像URL"
    )
    # 方案A：保留Enum（mysql数据库字段为enum类型）
    gender: Mapped[Optional[str]] = mapped_column(
        Enum("male", "female", "unknown"),
        default="unknown",
        comment="性别"
    )
    # 方案B（推荐，兼容性更好，直接用String）
    # gender: Mapped[Optional[str]] = mapped_column(
    #     String(10),
    #     default="unknown",
    #     comment="性别：male/female/unknown"
    # )
    bio: Mapped[Optional[str]] = mapped_column(
        String(500),
        default="这个人很懒，什么都没写~",
        comment="个人简介"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        comment="手机号"
    )
    # ✅ 不带括号！插入数据时动态执行now
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )

