import requests
from lxml import html
import csv
TMD_URL ="https://mars-coder.cn/interview/bank/33/"

def main():

        response = requests.get(TMD_URL)
        # 把数据存储在一个变量里，
        de_fs = html.fromstring(response.text)
        # 调用变量方法获取详细数据
        set_b=de_fs.xpath("//*[@id='app']/div/div/div/main/div/div/div[2]/div[1]/div[3]/div/div/div/div/text()")
        print(set_b)

main()


