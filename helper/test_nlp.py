from get_article_text import *
from nlp import get_countries
import urllib3
import inspect

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

links = open("../corona_data/corona_links.txt", 'r').readlines()
titles = open('../corona_data/corona_titles.txt','r').readlines()

for link, title in zip(links, titles):
	article_text = get_article_text(link)
	candidates_list = get_countries(article_text)
	print ("%s: %s" % (title.strip(), candidates_list)) 



