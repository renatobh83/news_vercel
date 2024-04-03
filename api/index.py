from cgitb import text
from os.path import dirname, join, abspath
import time
import re
import json
import scrapy
import multiprocessing
from scrapy.crawler import CrawlerProcess
from flask import Flask, render_template
import tempfile

dir = dirname(abspath(__file__))

app = Flask(__name__, template_folder=join(dir,'..', 'templates'))

temp_dir = tempfile.gettempdir()

file_path = join(temp_dir, 'news.json')

crawler_executado = False
tempo_atual = time.time()

class NewsSpider(scrapy.Spider):
    name = "news"
    custom_settings = {
        'USER_AGENT' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }


    def start_requests(self):
        yield scrapy.Request("https://valor.globo.com/ultimas-noticias/", callback = self.parse_valor)
        yield scrapy.Request("https://www1.folha.uol.com.br/ultimas-noticias/", callback = self.parse_folha)
        yield scrapy.Request("https://www.estadao.com.br/ultimas/", callback = self.parse_estadao)
        yield scrapy.Request("http://broadcast.com.br/", callback = self.parse_broadcast)
        yield scrapy.Request("https://www.bomdiamercado.com.br/noticias/", callback = self.parse_bdm)

    def parse_valor(self, response):
        noticias = response.css('div.bastian-feed-item')
        for noticia in noticias:
            yield {
                "noticia": noticia.css("h2>a::text").get(),
                "resumo": noticia.xpath(".//p[contains(@class, 'feed-post-body-resumo')]/text()").get(),
                "hora":  noticia.css('span.feed-post-datetime::text').get().strip(),
                "jornal": 'Valor'
            }


    def parse_folha(self, response):
        noticias = response.xpath('//li[contains(@class, "c-headline--newslist") and not(.//div[contains(@class, "OUTBRAIN")])]')[:7]
        for noticia in noticias:
             time = noticia.css('time.c-headline__dateline::text').get().strip()
             yield {
                "noticia": noticia.css('h2::text').get(),
                "resumo": noticia.xpath('.//p[contains(@class, "c-headline__standfirst")]/text()').get(),
                'hora':  time,
                "jornal": "Folha"
            }
    def parse_broadcast(self, response):
        noticias = response.css('div.materia')[1:6]
        for noticia in noticias:
            texto =noticia.css('h3 a::text').get()

            yield{
                "noticia": texto.capitalize(),
                "resumo": noticia.css('p.excerpt::text').get(),
                "jornal": "Broadcast +"
            }

    def parse_estadao(self, response):
        noticias = response.css('.noticias-mais-recenter--item')
        for noticia in noticias:
             yield {
                "noticia": noticia.css('h3::text').get(),
                "jornal": 'Estadao',
                'hora':  noticia.css('span.date::text').get()
            }
    def parse_bdm(self, response):
        noticias = response.css('div.col-md-12 .no-gutter-col')
        for noticia in noticias:
            yield{
                'noticia': noticia.css('.content a h4::text').get().strip(),
                'resumo': noticia.css('.content a p.small.content ::text').get().strip(),
                'hora': noticia.css('p.x-small::text').get().strip(),
                'jornal': 'BDM'
            }
        # yield scrapy.Request(
        #     'https://www.bomdiamercado.com.br/noticias/page/2/',
        #     callback=self.parse_bdm
        # )
def run_crawler():
    process = CrawlerProcess(settings={
        'FEEDS': {file_path: {'format': 'json', 'overwrite': True}},  # new in 2.1
        'LOG_ENABLED': True
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
    app.run(debug=False)