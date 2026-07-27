# a={"wzc","mys","llh","hcr"}
# b={"xch","yxx","syc","wzc","lzs"}
# c={"mys","llh","lzs"}
# d=c.intersection(a)
# print(d)
# a = {"马寅寿":90,"罗丽华":90}
# print(a["马寅寿"])
# are={}
# while True:
#     print("* * * * * * * * * * * * *")
#     print("* 1.  添  加  购  物     *")
#     print("* 2.  修  改  购  物     *")
#     print("* 3.  删  除  购  物     *")
#     print("* 4.  查  看  购  物     *")
#     print("* 5.  退  出  购  物     *")
#     print("* * * * * * * * * * * * *")
#     t=input("输入操作（1-5）:")
#     match t :
#         case "1":
#             a = input("请输入商品名字：")
#             b = input("输入商品价格：")
#             c = input("输入商品数量：")
#             if a in are:
#                 print("已经存在，重新输入")
#             else:
#                 are={"name":a,"price":b,"number":c}
#                 print("添加完成")
#         case "2":
#             pass
#         case "3":
#             pass
#         case "4":
#             a=input("")
#             print(are)
#         case "5":
#             pass
# def f(r):
#     """
#     这个是一个圆周的计算
#     """
#     area=3.14*r*2
#     return round(area),round(r**2)
# print(f(5))
# def f(sr):
#     sum = 0
#     for i in range(0,len(sr)):
#         if sr[i]=="a" or sr[i]=="e" or sr[i]=="i" or sr[i]=="o" or sr[i]=="u" or sr[i]=="A" or sr[i]=="E" or sr[i]=="I" or sr[i]=="O" or sr[i]=="U":
#             sum=sum+1
#             return sum
# sr=input("请输入字符串：")
# print(f(sr))
# scro_list=[1,3,5,8,2,4,6,65,2,32]
# def counts (scro_list) :
#     a=max(scro_list)
#     b=min(scro_list)
#     c=sum(scro_list)/len(scro_list)
#     return a,b,c
# print(counts(scro_list))
# num=100
# def main():
#     global num
#     num=num+1
#     return num
# print(main())
# def main(name,age,num):
#     print(f"注册成功！姓名：{name}，年龄：{age}，six：{num}")
#     return {"name":name,"age":age,"num":num}
# a=main("mys",20,"男")
# b=main("llh",20,"女")
# print(a,"\n",b)
# date_a=["sada","mys","llh","w"]
# date_a.sort(key=len,reverse=True)
# print(date_a)
# def main(n):
#     if n==1:
#         return 1
#     else:
#         return n*main(n-1)
# a=main(3)
# print(a)
from sys import flags

# a=200
# score=92.2
# hob="py"
# flag=1
















