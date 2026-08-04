

# with open("01.csv","w",encoding="GBK") as f:
#     f.write("姓名,年龄,性别,爱好\n")
#     f.write("小王,19,男,开车\n")
#     f.write("小马,18,男,弹琴\n")

with open("01.csv","r",encoding="GBK") as f:
    for s in f:
        print(s.strip())