from  lxml import html
with open("ai简历4.html","r",encoding="utf-8") as f:
    html_text = f.read()
#解析html文本，将其转换为一个html文本对象
    document = html.fromstring(html_text)

    tt_list = document.xpath("//header/div/span/text()")
    print(tt_list)

    td_list = document.xpath("//section[1]/div/span/text()")
    print(td_list)
