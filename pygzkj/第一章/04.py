# import random
# from until import mat_a
# from until import mat_a
# from until import mat_b
# b=mat_b.main_1()
# a=mat_a.man_1()
# class f:
#     pass
# c1=f()
# c1.name="mys"
# c1.age=20
# print(c1.__dict__)
# class SoLut:
#     shops=20
#     def __init__(self,num,name,age):
#         self.num=num
#         self.name=name
#         self.age=age
#     def f(self):
#         print(self.num,self.name,self.age)
#     def g(self,a,b):
#         """
#         表示num*age*a*b的值
#         :param a:
#         :param b:
#         :return:
#         """
#         c=self.num*a*b*self.age
#         return c
#     def __str__(self):
#         return str(self.num)+' '+self.name+' '+str(self.age)
#     def __le__(self, other):
#         return self.age<other.age
#     def __gt__(self, other):
#         return self.age>other.age
# c1=SoLut(1,"llh",20)
# d=c1.g(1,2)
# c2=SoLut(1,"mys",21)
# if c1<c2:
#     print(f"{c1.name} 年龄小于 {c2.name}")
# print(c1)
class Student:
    student_list = []
    def __init__(self, name, age, yw_score,sx_score,yy_score):
        self.name = name
        self.age = age
        self.yw_score = yw_score
        self.sx_score = sx_score
        self.yy_score = yy_score
    def __str__(self):
        return self.name+"  年龄|"+str(self.age)+"  语文|"+str(self.yw_score)+"  数学|"+str(self.sx_score)+"  英语|"+str(self.yy_score)
    def __lt__(self, other):
        return self.age<other.age
    def __le__(self, other):
        return self.yw_score<other.yw_score or self.sx_score<other.sx_score or self.yy_score<other.yy_score
    def score1(self,a,b,c):
        if a is not None :
            self.yw_score=a
        if b is not None :
            self.sx_score=b
        if c is not None :
            self.yy_score=c

    @classmethod
    def student_change1(self):
        name = input("请输入查找学生姓名:")
        for s in self.student_list:
            if name == s.name:
                print(f"学生当前信息: {s}")
                chine=int(input("请输入修改语文成绩:"))
                math= int(input("请输入修改数学成绩:"))
                english= int(input("请输入修改英语成绩:"))
                if 0<=chine<=100 and 0<=math<=100 and 0<=english<=100:
                    s.score1(chine,math,english)
                    print("成功修改！")
                    print(f"学生修改后的信息: {s}")
                    return
                else:
                    print("成绩必须在0~100以内")
                    return
        print("未找到该学生")
    @classmethod
    def student_del(self):
        name = input("请输入查找学生姓名:")
        for s in self.student_list:
            if name == s.name:
                s.student_list.remove(s)
                print("成功删除！")
                return
        print("未查找到学生:")


    @classmethod
    def student_add(cls):  # 把 self 换成 cls
        name = input("请输入学生姓名:")
        for s in cls.student_list:  # 用 cls 访问类变量
            if name == s.name:
                print(f"{s.name} 同学已经存在库里")
                return
        # 注意：下面的输入逻辑应放在循环外面，否则会重复提示

        age = int(input("请输入学生年龄:"))
        yw_score = int(input("请输入学生语文成绩:"))
        sx_score = int(input("请输入学生数学成绩:"))
        yy_score = int(input("请输入学生英语成绩:"))
        if 0 <= yw_score <= 100 and 0 <= sx_score <= 100 and 0 <= yy_score <= 100:
            sst = Student(name, age, yw_score, sx_score, yy_score)
            cls.student_list.append(sst)
            print("添加学生信息成功")
        else:
            print("添加学生信息失败，成绩需要在0~100以内")

    @classmethod
    def student_seek(self):
        name = input("请输入查找学生姓名:")
        for s in self.student_list:
            if name == s.name:
                print(f"学生信息: {s}")
                return

        print("没有找到该学生")

while True:
    a="""
                                 欢迎来到教务系统
    ************************************************************************
    *    1.添加学生  2.修改学生信息  3.删除学生信息  4.查询学生信息  5.退出系统     *
    ************************************************************************
    """
    print(a)
    see=input("请输入操作(1-5):")
    try:
        match see :
            case "1":
                Student.student_add()
            case "2":
                Student.student_change1()
            case "3":
                Student.student_del()
            case "4":
                Student.student_seek()
            case "5":
                break
            case _:
                print("输入错误")
    except Exception:
        print("系统出错")