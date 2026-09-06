from fastapi import HTTPException
from pymysql import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

from schemas.exception import http_exception_handler, integrity_error_handler, sqlalchemy_error_handler


def register_exception_handlers(app):
    """
    注册全局异常处理
    :param app:
    :return:
    """
    app.add_exception_handler(HTTPException,http_exception_handler)
    app.add_exception_handler(IntegrityError,integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError,sqlalchemy_error_handler)
    app.add_exception_handler(Exception,sqlalchemy_error_handler)


