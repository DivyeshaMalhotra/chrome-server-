from bs4 import BeautifulSoup
import requests

def get_article_text(link):
    response = requests.get(link, verify=False)
    soup = BeautifulSoup(response.text, "lxml")

    article = ""
    texts = soup.findAll('p', {'class': 'css-exrw3m evys1bk0'})
    for text in texts:
        article += (" " + text.text)
        
    article = article.lstrip()
    
    return article
