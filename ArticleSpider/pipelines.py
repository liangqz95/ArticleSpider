# -*- coding: utf-8 -*-


from scrapy.pipelines.images import ImagesPipeline
import codecs
import json
from scrapy.exporters import JsonItemExporter
import MySQLdb
from twisted.enterprise import adbapi
import MySQLdb.cursors

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class JsonWithEncodingPipeline(object):
    #自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json','w',encoding="utf-8")
    def process_item(self, item, spider):
        lines = json.dumps(dict(item),ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item
    def spider_closed(self,spider):
        self.file.close()

class JsonExporterPipeline(object):
    #使用scrapy提供的json exporter到处json文件
    def __init__(self):
        self.file = open('articleexport.json','wb')
        self.exporter = JsonItemExporter(self.file,encoding='utf-8',ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self,spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class MysqlPipeline(object):
    #使用同步的机制写入mysql
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1','root','123456','article_spider',charset='utf8',use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole_article(title, url, create_date, fav_nums)
            VALUES (%s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql,(item['title'],item['url'],item['create_date'],item['fav_nums']))
        self.conn.commit()

class MysqlTwistedPipeline(object):
    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls,settings):
        dbparms = dict(
        host = settings['MYSQL_HOST'],
        user = settings['MYSQL_USER'],
        password = settings['MYSQL_PWD'],
        db = settings['MYSQL_DBNAME'],
        charset = "utf8",
        cursorclass = MySQLdb.cursors.DictCursor,
        use_unicode = True
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert,item)
        query.addErrback(self.handle_error) #处理异常

    def handle_error(self,failure):
        #处理异步插入的异常
        print(failure)

    def do_insert(self,cursor,item):
        #执行具体的插入
        insert_sql = """
                    insert into jobbole_article(title, url, create_date, fav_nums,url_object_id,front_image_url,comment_nums,praise_nums,tags,content)
                    VALUES (%s, %s, %s,%s,%s,%s,%s,%s,%s,%s)
                """
        cursor.execute(insert_sql, (item['title'], item['url'], item['create_date'], item['fav_nums'],item['url_object_id'],item['front_image_url'],item['comment_nums'],item['praise_nums'],item['tags'],item['content']))

class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            for ok,value in results:
                image_file_path = value["path"]
                item['front_image_path'] = image_file_path

        return item
