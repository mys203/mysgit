import json

a={
    "name":"罗丽华",
    "age":21,
    "gender":"女"
}
s=json.dumps(a,ensure_ascii=False)
print(s)

json_str = [
{
    "name":"罗丽华",
    "age":21,
    "gender":"女"
},
{
    "name":"马寅寿",
    "age":21,
    "gender":"男"
},
{
    "name":"wzc",
    "age":21,
    "gender":"男"
}
]
O= json.load(json_str,ensure_ascii=False)
print(O)