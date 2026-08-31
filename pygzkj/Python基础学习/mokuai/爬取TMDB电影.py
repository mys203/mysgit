import requests
from lxml import html
import csv
TND_URL ="https://www.themoviedb.org"
TMD_URL = "https://www.themoviedb.org/movie/top-rated"
TMD_URL_1="https://www.themoviedb.org/discover/movie/items"

def movie_get(movie_b):
    # 发送请求
    movie_response=requests.get(movie_b,timeout=60)
    # 把数据存储在一个变量里
    movie_h = html.fromstring(movie_response.text)
    # 调用变量方法获取详细数据

    #电影信息
    name_a= movie_h.xpath("//*[@id='original_header']/div[2]/section/div[1]/h2/a/text()")
    name_year = movie_h.xpath("//*[@id='original_header']/div[2]/section/div[1]/h2/span/text()")
    name_date=movie_h.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[2]/text()")
    name_type=movie_h.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[3]/a/text()")
    name_time=movie_h.xpath("//*[@id='original_header']/div[2]/section/div[1]/div/span[4]/text()")
    name_scores=movie_h.xpath("//*[@id='consensus_pill']/div/div[1]/div/div/@data-percent")
    name_languages=movie_h.xpath("//*[@id='media_v4']/div/div/div[2]/div/section/div[1]/div/section[1]/p[3]/text()")
    name_director=movie_h.xpath("//*[@id='original_header']/div[2]/section/div[3]/ol/li[1]/p[1]/a/text()")
    name_novel=movie_h.xpath("//*[@id='original_header']/div[2]/section/div[3]/ol/li[2]/p[1]/a/text()")
    name_state = movie_h.xpath("//*[@id='original_header']/div[2]/section/div[3]/div/p/text()")

    dict_all={
        "电影名称":name_a[0].strip()if name_a else "",
        "年份":name_year[0].strip()if name_year else "",
        "上映时间":name_date[0].strip()if name_date else "",
        "类型":"，".join(name_type)if name_type else "",
        "时长":name_time[0].strip()if name_time else "",
        "评分":name_scores[0].strip()if name_scores else "",
        "语言":name_languages[0].strip()if name_languages else "",
        "导演":"，".join(name_director)if name_director else "",
        "作者":"，".join(name_novel)if name_novel else "",
        "简介":name_state[0].strip()if name_state else "",
    }
    return dict_all




def save_s(all_movie):
    with open('第二次抓取电影网站数据.csv','w',encoding='utf-8-sig',newline="") as f:
        writer = csv.DictWriter(f,fieldnames=["电影名称","年份","上映时间","类型","时长","评分","语言","导演","作者","简介"])
        writer.writeheader()
        writer.writerows(all_movie) #写入文件

all_movie=[]
def main():
    for page_num in range(1,6):
        # 发送请求
        if page_num == 1:
            response = requests.get(TMD_URL, timeout=60)
        else:
            response = requests.post(TMD_URL_1,
                                     f"air_date.gte=&air_date.lte=&certification=&certification_country=CN&debug=&first_air_date.gte=&first_air_date.lte=&include_adult=false&include_softcore=false&latest_ceremony.gte=&latest_ceremony.lte=&page={page_num}&primary_release_date.gte=&primary_release_date.lte=&region=&release_date.gte=&release_date.lte=2027-02-02&show_me=everything&sort_by=vote_average.desc&vote_average.gte=0&vote_average.lte=10&vote_count.gte=300&watch_region=CN&with_genres=&with_keywords=&with_networks=&with_origin_country=&with_original_language=&with_watch_monetization_types=&with_watch_providers=&with_release_type=&with_runtime.gte=0&with_runtime.lte=400",
                                     timeout=60)
        # 把数据存储在一个变量里，
        de_fs = html.fromstring(response.text)
        # 调用变量方法获取详细数据
        #set_b = de_fs.xpath("/html/body/div[2]/main/section/div/div/div/div[2]/div[2]/div/section/div/div/div[1]/div/div[@class='w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-colors hover:border-gray-300']")
        set_b=de_fs.xpath(f"//*[@id='page_{page_num}']/div/div/div")
        for row in set_b:
            movie_a=row.xpath("./div/div/a/@href")
            if movie_a:
                #电源详情的url地址
                # movie_b=TND_URL + movie_a
                print(TND_URL+movie_a[0],"获取电影详情...")
                movie_b=TND_URL+movie_a[0]
                #获取电源的数据方法
                a_get=movie_get(movie_b)
                #存储在列表里
                all_movie.append(a_get)
            #存储到csv文件里操作
    print("正在存储到文件csv中")
    save_s(all_movie)



if __name__ == '__main__':
    main()


