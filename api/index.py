import os
import time
import json
import scrapy
import multiprocessing
from scrapy.crawler import CrawlerProcess
from flask import Flask, render_template
import tempfile

app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'))

temp_dir = tempfile.gettempdir()

file_path = os.path.join(temp_dir, 'news.json')

# file_path = os.path.join(os.path.dirname(__file__), 'news.json')
crawler_executado = False
tempo_atual = time.time()

class NewsSpider(scrapy.Spider):
    name = "news"
    custom_settings = {
        'USER_AGENT' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }
    def start_requests(self):
        yield scrapy.Request("https://valor.globo.com/ultimas-noticias/", callback = self.parse_valor)
        yield scrapy.Request("https://www1.folha.uol.com.br/ultimas-noticias", callback = self.parse_folha)
        yield scrapy.Request("https://www.estadao.com.br/ultimas/", callback = self.parse_estadao)
    def parse_valor(self, response):
        # noticias = response.css("h2>a::text").getall()
        noticias = response.css('div.bastian-feed-item')
        # hora = response.css('span.feed-post-datetime::text').get()
        for noticia in noticias:
            yield {
                "noticia": noticia.css("h2>a::text").get(),
                "hora":  noticia.css('span.feed-post-datetime::text').get().strip(),
                "jornal": 'Valor'
            }
    def parse_folha(self, response):
        # noticias = response.css("h2::text").getall()[1:]
        noticias = response.css('li.c-headline--newslist')
        for noticia in noticias:
            #  time = noticia.css('time.c-headline__dateline::text').get().strip()
             yield {
                "noticia": noticia.css('h2::text').get(),
                # 'Hora':  time if time else tempo_atual
                "jornal": "Folha"
            }
    def parse_estadao(self, response):
        noticias = response.css("h3::text").getall()
        for noticia in noticias:
             yield {
                "noticia": noticia,
                "jornal": 'Estadao'
            }
def run_crawler():
    process = CrawlerProcess(settings={
        'FEEDS': {file_path: {'format': 'json', 'overwrite': True}},  # new in 2.1
        'LOG_ENABLED': False
    })

    process.crawl(NewsSpider)
    process.start()


def ler_arquivo():
    global crawler_executado
    with open(file_path,'r') as f:
        data = json.load(f)
        crawler_executado = False
        return data

@app.route('/')
def get_offers():
    global crawler_executado

    # Verificar se o crawler já foi executado
    if not crawler_executado:
        # Executar o crawler apenas se ainda não foi executado
        p = multiprocessing.Process(target= run_crawler)
        p.start()
        p.join()
        crawler_executado = True

    # Ler e retornar dados do arquivo JSON
    data = ler_arquivo()

    # return data
    return render_template('index.html', json_data=data)

if __name__ == '__main__':
    # Executar o aplicativo Flask no modo de desenvolvimento
    app.run(debug=True)