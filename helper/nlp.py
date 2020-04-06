from collections import Counter
import spacy
import json
import pandas as pd
import pycountry
import en_core_web_sm
import inspect
nlp = en_core_web_sm.load()

# name of file importing and calling function 
f_name = inspect.stack()[-1].filename.split("/")[-1]

if f_name == "app.py":

    # populate US state abbreviation dictionary with abbreviations as the keys
    f = open('corona_data/us_state_abbrev.csv', 'r')
    us_state_abbrev = {}
    for line in f:
        line_list = line.strip().split(',')
        us_state_abbrev[line_list[0]] = line_list[1]

    # populate demonym dataframe
    f = open('corona_data/demonyms.txt', 'r')
    lines = [line.split("\t")[:3] for line in f]
    demonyms_df = pd.DataFrame(lines, columns=['GPE', 'NORP_singular', 'NORP_plural'])

    # populate corona charities dataframe and create unique id
    charities_df = pd.read_json('corona_data/corona_data.json')
    charities_df['id'] = range(1,charities_df.shape[0]+1) # create unique id for each charity 

# modified for test.py
else:

    # populate US state abbreviation dictionary with abbreviations as the keys
    f = open('../corona_data/us_state_abbrev.csv', 'r')
    us_state_abbrev = {}
    for line in f:
        line_list = line.strip().split(',')
        us_state_abbrev[line_list[0]] = line_list[1]

    # populate demonym dataframe
    f = open('../corona_data/demonyms.txt', 'r')
    lines = [line.split("\t")[:3] for line in f]
    demonyms_df = pd.DataFrame(lines, columns=['GPE', 'NORP_singular', 'NORP_plural'])

    # populate corona charities dataframe and create unique id
    charities_df = pd.read_json('../corona_data/corona_data.json')
    charities_df['id'] = range(1,charities_df.shape[0]+1) # create unique id for each charity  


def convert_nationalities(entities):
    """ convert demonyms (nationalities) to countries using demonym dataframe """
    
    locs = []

    for text, label in entities:

        if label == "NORP":
            try:
                loc = demonyms_df[(demonyms_df['NORP_singular'] == text) | \
                                  (demonyms_df['NORP_plural'] == text)].iloc[0,0]
            except:
                continue

        else:
            loc = text

        locs.append(loc)
        
    return locs


def filter_candidates(candidates):
    """ convert abbreviations and various locations (cities, states, etc.) to countries """

    country_dict = {}

    for candidate in candidates:

        if "the" in candidate[0]:
            place_revised =  candidate[0].replace("the", "").lstrip()
            candidate = (place_revised, candidate[1])

        if "." in candidate[0] or len(candidate[0]) <= 3:
            abbrev = "".join(candidate[0].split("."))

            if len(abbrev) == 2:
                # is a us state 
                if abbrev in us_state_abbrev.keys():
                    country = "United States"

                else:
                    try:
                        country = pycountry.countries.get(alpha_3=abbrev).name
                    
                    except:
                        continue 

                if country not in country_dict:
                    country_dict[country] = 0

                country_dict[country] += candidate[1]

                continue

            if len(abbrev) == 3:
                # is a us state 
                if abbrev in us_state_abbrev.keys():
                    country = "United States"

                else:
                    try:
                        country = pycountry.countries.get(alpha_3=abbrev).name
                    
                    except:
                        continue 

                if country not in country_dict:
                    country_dict[country] = 0

                country_dict[country] += candidate[1]

                continue

        try:
            country = pycountry.countries.search_fuzzy(candidate[0])[0].name

            if country not in country_dict:
                country_dict[country] = 0

            country_dict[country] += candidate[1]

        except:
            continue

    return list(country_dict.items())


def get_countries(article_text):
    """ get top 3 country mentions in article text with their counts """

    # text with entity label
    items = [(x.text, x.label_) for x in nlp(article_text).ents if x.label_ == "GPE" or x.label_ == "NORP"]

    # locs = [item[0] for item in items]
    locs = convert_nationalities(items) # convert demonyms and return list of locations 

    candidates = Counter(locs).most_common(3)

    candidates_filtered = sorted(filter_candidates(candidates), key=lambda x: x[1], reverse=True)

    # no countries found
    if len(candidates_filtered) == 0:
        print ("no countries found")
        candidates_filtered = [('United States', 1)]

    # take top 3
    # if len(candidates_filtered) >= 3:
    #     candidates_filtered = candidates_filtered[:3]

    # return a list of tuples
    return candidates_filtered


def get_charities(country_counts, amount):
    """ get charities from database proportionately for each country.
    if no countries, then return charities from US. """
    
    country_charities_dict = {}

    for country in country_counts.keys():
    
        charities_filtered = charities_df[charities_df['country'] == country]

        if charities_filtered.shape[0] == 0:
            continue

        # sort by ratio
        # charities_filtered = charities_filtered.sort_values(by='ratio', ascending=False)
        
        ratio = country_counts[country] / sum(country_counts.values())
        max_obs = round(ratio * amount)

        # display no charities for this country since not mentioned enough 
        if max_obs == 0:
            continue

        if charities_filtered.shape[0] > max_obs:
            charities_filtered = charities_filtered.iloc[:max_obs,:]

        # shuffle rows
        charities_filtered = charities_filtered.sample(frac=1)

        country_charities_dict[country] = charities_filtered
        
    desired_charities = pd.concat(country_charities_dict.values())
    
    # reduce charity size if too large
    if desired_charities.shape[0] > amount:
        desired_charities = desired_charities.iloc[:amount,:]
    
    # fill missing charities with US ones
    elif desired_charities.shape[0] < amount:
        
        extra_amount = amount - desired_charities.shape[0]
        extra_charities = charities_df[(charities_df['country'] == "United States") & \
                  (~charities_df['id'].isin(desired_charities['id']))]
        
        extra_charities = extra_charities.sort_values(by='ratio', ascending=False).iloc[:extra_amount,:]
        
        desired_charities = pd.concat([desired_charities, extra_charities])
        
    return desired_charities


def full_json(article_text):
    """ return a specified amount of charities that are relevant to the inputed article """

    candidates_list = get_countries(article_text)
    charity_amount = 6

    country_counts = dict(candidates_list)
    country_counts_copy = country_counts.copy()

    for country in country_counts_copy.keys():
        if country not in set(charities_df['country']):
            country_counts.pop(country, None)

    desired_charities = get_charities(country_counts, charity_amount)
    desired_charities_dict = desired_charities.to_dict(orient="records")
    
    return desired_charities_dict


