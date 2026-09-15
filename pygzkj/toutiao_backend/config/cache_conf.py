import redis.asyncio as redis


#基本功能都写完了，就写Redis的配置，加快运行

REDIS_URL = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
redis_client=redis.Redis(
    host=REDIS_URL,  # Redis服务器的主机地址
    port=REDIS_PORT, #Redis的端口号
    db=REDIS_DB, #Redis,数据的编号
    decode_responses=True  #是否将数据解码为字符串·

)