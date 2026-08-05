# a=int(input())
# b=int(input())
# c=input("请输入+、-、/、*：")
# match c :
#     case "+" :
#         print(a+b)
#     case "-" :
#         print(a-b)
#     case "*" :
#         print(a*b)
#     case "/" :
#         print(a/b)
#     case _ :
#         print("输入c不正确")
# su=0
# for i in range(100,500):
#     if i%3==0:
#         su=su+i
# else:
#     print(su)
# a=int(input())
# b=int(input())
# for i in range(a):
#     for j in range(b):
#         print(" *",end="")
#     print()
# a=int(input())
# b=int(input())
# for i in range(0,a):
#     for j in range(1,i+1):
#         print(f" {j} × {i} = {j*i}",end="")
#     print()
# p=1
# while p==1:
#     a=input("请输入用户名：")
#     b= input("请输入密码：")
#     if a=="admin" and b=="123":
#         print("登录成功，进入b站")
#         p = 0
#     elif a=="mys" and b=="321":
#         print("登录成功，进入b站")
#         p=0
#     elif a=="" or b=="":
#         print("输入的用户名或密码不能为空!请重新输入")
#     else:
#         print("登录失败，请重新输入")
# import random
# a=random.randint(1,100)
# while True:
#     c = int(input("输入一个数:"))
#     if c>a:print("dal")
#     elif c<a:
#         print("小了")
#     else:
#         print("成了")
#         break
# s=["a","b","c"]
# print(s[:-1])
# s=[1,3,4,2]
# s.sort()
# print(s)
# s.reverse()
# print(s)
# print(sum(s)/len(s))
# s=[12,32,45,77,80,92,33,57,97,98]
# a=[]
# for x in s:
#     print(x,end=" ")
#     a.append(x**2)
# print(a)
# s="hello-people"
# a=s.upper()
# print(a)
# mail=input("请输入邮箱:")
# if mail.count("@")==1 and mail.count(".")==1:
#     print("是正确的邮箱")
# else:
#     print("错误的邮箱")
# t1=1,2,3,4,5,6
# print(t1)
# a,*b,c,d=t1
# print(a,c,d)
# a=1
# b=2
# a,b=b,a
# print(a,b)
s=("1","mys")