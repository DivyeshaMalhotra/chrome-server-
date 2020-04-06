import requests
from bs4 import BeautifulSoup
import re
import json
import urllib3
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

global_url = 'https://www.globalgiving.org/'

def getInfoFromPage(post_url, picture_url):

    response = requests.get(post_url, verify=False)
    html = response.text
    soup = BeautifulSoup(html, "lxml")

    recognitions = soup.findAll('span', {'class': 'box_leftPadded3'})

    if len(recognitions) == 0:
        raise Exception('no recognitions')

    recognitions_text = [r.getText() for r in recognitions]

    if len(list(filter(lambda r: 'Vetted' in r, recognitions_text))) == 0:
        raise Exception('not vetted')

    if "Top Ranked" in recognitions_text:
        top_ranked = "1"

    else:
        top_ranked = "0"
    
    description = soup.find('p', {'class': 'text_fontSizeLarge'}).getText()
    
    project_name = soup.find('h1', {'class': 'box_verticalPaddedHalf'}).getText()
    
    charity = soup.find('span', {'class': 'col_ggPrimary5Text'})
    
    charity_name = charity.find('a').getText()
    
    charity_link = charity.find('a').get('href')
    
    donate_link = soup.find('div', {'class': "grid-12 grid-md-6 grid-lg-4 box_padded1"}).find('a').get('href')
    
    headings = []
    categories = soup.findAll('a', {'class': 'proj_meta layout_centerVertical box_horizontalPadded1 '
                                             'text_fontSizeSmall col_ggSecondary1LightText text_7i'})
    ###PROBLEM
    raised = soup.find('span', {'class': 'text_7n text_fontSizeLargest col_ggPrimary3Text js-currencyTitle js-projectFunding js-ambigCurrencyFlag'}).getText()
    goal = soup.find('span', {'class': 'js-currencyTitle js-projectGoal js-ambigCurrencyFlag'}).getText()
    donations = soup.find('span', {'class': 'col_ggPrimary5Text text_7n'}).getText()
    
    for i in categories:
        headings.append(i.getText())

    theme = headings[0]
    country = headings[1]

    # print (project_name+"\n")

    final = {"description": description,
             "project_name": project_name,
             "charity_name": re.sub('\W+',' ',charity_name).lstrip().rstrip(),
             "charity_link": global_url + charity_link,
             "theme": re.sub('\W+',' ',theme).lstrip().rstrip(),
             "country": re.sub('\W+',' ', country).lstrip().rstrip(),
             "goal": goal,
             "raised": raised,
             "donations": donations,
             "donate_link": global_url + donate_link,
             "picture_link": picture_url,
             "top_ranked": top_ranked}

    return final

def getAllLinks(url):
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, "lxml")

    post_links = []
    picture_links = []

    posts = soup.findAll('a', {'class': 'col_inherit text_letterSpacingNormal js-projTitle'})
    pictures = soup.findAll('a', {'class': 'grid-12 grid-lg-4 grid-parent img-bg img-bg-cover img-minHeight_short img-emphasizeOnHover'})
    
    for i in range(len(posts)):
        post_links.append(global_url+posts[i]['href'][1:])
        picture_style = pictures[i]['style']
        picture_links.append(global_url+picture_style[picture_style.find("(")+1:picture_style.find(")")])

    return post_links, picture_links

def getCount(url):
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, "lxml")

    element_above = soup.find('select', {'class': 'input_preventDisplay input_searchSelect border_default box_horizontalPadded1 box_verticalMargin1 text_8n js-size'})
    count = int(element_above.next_sibling.strip().split()[1])

    return count

def getCoronaCharities(charity_list):

    charities_df = pd.DataFrame(charity_list)

    charities_filtered = charities_df.copy()

    terms = ["corona", "covid"]

    corona_charities = []
        
    for term in terms:

        corona_charities.append(charities_filtered[charities_filtered['project_name'].str.contains("(?i)" + term)])
        charities_filtered = charities_filtered[~charities_filtered['project_name'].str.contains("(?i)" + term)]

    corona_charities_df = pd.concat(corona_charities)

    # temporary - change scraping code to calculate ratio
    corona_charities_df['ratio'] = corona_charities_df['raised'].str.replace(',','').str[1:].astype(float) / \
    corona_charities_df['goal'].str.replace(',','').str[1:].astype(float)

    return corona_charities_df


def main():

    count = getCount('https://www.globalgiving.org/search/') - 1

    search_page = 'https://www.globalgiving.org/search/?size=%d&nextPage=1&sortField=sortorder&loadAllResults=true' % count
    post_links, picture_links = getAllLinks(search_page)

    all_data = []

    for i in range(10):

        post_link = post_links[i]
        picture_link = picture_links[i]
        
        try:
            print (i+1)
            all_data.append(getInfoFromPage(post_link, picture_link))

        except:
            continue

    # export all charities
    with open('Data/all_charities.json', 'w') as outfile:
        outfile.write(json.dumps(all_data, indent=4, separators=(',', ': ')))

    corona_charities_df = getCoronaCharities(all_data)

    # export coronavirus charities 
    with open('../corona_data/corona_data.json', 'w') as f:
        json.dump(corona_charities_df.to_dict('records'), f)

    return None
    
if __name__ == "__main__":
    main()

             
    
    
