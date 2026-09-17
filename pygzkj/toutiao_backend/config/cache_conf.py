from typing import Any

import redis.asyncio as redis
import json

#基本功能都写完了，就写Redis的配置，加快运行

REDIS_URL = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

#创建redis的对象
redis_client=redis.Redis(
    host=REDIS_URL,  # Redis服务器的主机地址
    port=REDIS_PORT, #Redis的端口号
    db=REDIS_DB, #Redis,数据的编号
    decode_responses=True,  #是否将数据解码为字符串·
    socket_connect_timeout=2,  #连接超时2秒，Redis挂了不拖垮接口
    socket_timeout=2,  #读写超时2秒
)

#获取字符串的缓存方法
async def get_redis_client(key:str):
    try:
        return await redis_client.get(key)  #用上面的对象来操作，直接变成字符串
    except Exception as e:
        print(f"获取缓存失败:{e}")
        return None


#获取:列表或字典
async def get_redis_json(key:str):
    try:
        data= await redis_client.get(key)
        #如果有数据就返回
        if data:
            return json.loads(data) #把字符串改为序列化的json数据
        else:
            return None
    except Exception as e:
        print(f"获取JSON缓存失败:{e}")
        return None



#设置缓存set
async def set_cache(key:str,value:Any,expire:int=3600):
    try:
        if isinstance(value,(dict,list)):
            #转字符串
            value = json.dumps(value)   #这个是转字符串操作跟上面loads类似
        await redis_client.setex(key, expire,value)
        return True
    except Exception as e:
        print(f"设置缓存失败:{e}")
        return False

