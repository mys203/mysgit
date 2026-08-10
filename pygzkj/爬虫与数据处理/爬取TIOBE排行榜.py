import requests
from lxml import html
target_url = "https://www.tiobe.com/tiobe-index/"
#发送请求，获取数据
response = requests.get(target_url)

document = html.fromstring(response.text)
targ=document.xpath("/html/body/section/div/article/h1/b/text()")
print(targ)
#解析数据
tc_text=document.xpath("//*[@id='top20']/thead/tr/th/text()")
print(tc_text)

tt_text=document.xpath("//table[@id='top20']/tbody/tr")
for tt in tt_text:
    td=tt.xpath("./td/text()")
    print(td)


