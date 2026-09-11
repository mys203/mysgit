# models/users.py —— 用户相关表：用户表(user)、令牌表(user_token)

# 导入 datetime 类，用来给时间字段做类型标注
from datetime import datetime
# 导入 Optional，用来表示“这个字段可以是 None（可空）”
from typing import Optional

# 导入 SQLAlchemy 声明式映射的三件套：
#   DeclarativeBase —— 声明式基类，模型类继承它才能映射成表
#   Mapped           —— Python 侧的类型注解（标注这一列是什么 Python 类型）
#   mapped_column    —— 用来定义数据库列（类型、约束等）
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 导入常用的数据库列类型和约束：
#   Index      建索引    Column 列（本项目里其实没用到，可删）
#   Integer    整数      String 字符串     DateTime 时间
#   Enum       mysql枚举类型    ForeignKey 外键
from sqlalchemy import Index, Column, Integer, String, DateTime, Enum, ForeignKey


class Base(DeclarativeBase):
    """所有模型类的基类：继承它，Python 类就会被识别成一张数据库表"""
    pass  # 这里不需要额外内容，只作为“基类”存在


class User(Base):
    """用户表：一个类 = 一张表，一个属性 = 一个字段"""

    __tablename__ = 'user'  # 指定数据库里的表名（可以和类名 User 不同）

    # __table_args__ 是表级别的设置，这里放索引
    # 给常查询的字段建索引，查询时不用全表扫描，能加快速度、减轻服务器压力
    __table_args__ = (
        Index('idx_user', 'username'),        # 给 username 列建索引
        Index('idx_user_email', 'phone'),     # 给 phone 列建索引
    )

    # ============ 下面是 User 表的字段（列） ============

    # id 主键：Mapped[int] 声明 Python 类型，mapped_column(...) 定义数据库列
    id: Mapped[int] = mapped_column(
        Integer,             # 数据库列类型：整数
        primary_key=True,    # 主键，唯一标识一行
        autoincrement=True,  # 自增，插入时数据库自动 +1
        comment="用户ID"     # 字段注释，写进建表语句
    )

    username: Mapped[str] = mapped_column(
        String(50),       # 字符串类型，最大长度 50
        unique=True,      # 唯一约束：用户名不能重复
        nullable=False,   # 非空：必须有值
        comment="用户名"
    )

    password: Mapped[str] = mapped_column(
        String(255),      # 存的是加密后的密文（哈希值较长），给 255 长度
        nullable=False,   # 非空
        comment="密码（加密存储）"
    )

    # Optional[str] 表示这一列可空（可空时可不写 nullable，默认按可空处理）
    nickname: Mapped[Optional[str]] = mapped_column(
        String(50),       # 字符串，最大长度 50
        comment="昵称"
    )

    avatar: Mapped[Optional[str]] = mapped_column(
        String(255),      # 字符串，最大长度 255
        # default：插入时如果没传这个字段，就用这个默认头像 URL
        default="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
        comment="头像URL"
    )

    # 方案A：用 Enum，数据库里这个字段是 mysql 的 enum 类型
    gender: Mapped[Optional[str]] = mapped_column(
        Enum("male", "female", "unknown"),  # 只允许这三个值之一
        default="unknown",                  # 默认值 unknown
        comment="性别"
    )
    # 方案B（推荐，兼容性更好，直接用 String 代替 Enum）
    # gender: Mapped[Optional[str]] = mapped_column(
    #     String(10),
    #     default="unknown",
    #     comment="性别：male/female/unknown"
    # )

    bio: Mapped[Optional[str]] = mapped_column(
        String(500),                        # 个人简介，最长 500
        default="这个人很懒，什么都没写~",  # 默认简介
        comment="个人简介"
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(20),   # 手机号，最长 20
        unique=True,  # 唯一：手机号不能重复
        comment="手机号"
    )

    # ✅ default=datetime.now 不带括号！传的是“函数本身”，插入时才动态算当前时间
    #   如果写成 datetime.now()，会在导入文件时就执行一次，所有行都会是同一个固定时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime,            # 时间类型
        default=datetime.now,  # 插入时默认填当前时间
        comment="创建时间"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,            # 时间类型
        default=datetime.now,  # 插入时默认填当前时间
        onupdate=datetime.now, # 每次更新(update)时自动刷新为当前时间
        comment="更新时间"
    )


class UserToken(Base):
    """用户令牌表：登录后生成的 token，用来验证登录状态"""
    __tablename__ = 'user_token'  # 表名

    # 表级别设置：给 token、user_id 建索引
    __table_args__ = (
        Index('token_UNIQUE', 'token'),        # 给 token 列建索引
        Index('fk_user_token_user_idx', 'user_id'),  # 给 user_id 列建索引
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="令牌ID")  # 主键自增
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False, comment="用户ID")  # 外键，指向 user.id，表示这个 token 属于哪个用户
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="令牌值")  # 令牌值，唯一
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")  # 过期时间，判断登录是否失效
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")  # 创建时间

    def __repr__(self):  # 只影响 print 打印效果，和数据库无关
        return f"<UserToken(id={self.id}, user_id={self.user_id}, token='{self.token}')>"  # 打印对象时的显示格式
