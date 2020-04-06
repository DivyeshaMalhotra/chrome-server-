from flask import Flask, request, jsonify
from helper.nlp import full_json
from helper.get_article_text import get_article_text

app = Flask(__name__)


@app.route('/get_charities', methods=['POST'])
def get_charities():
    print("JSON REQUEST", request.json)
    print("FORM REQUEST", request.form)
    article_name = request.json['article_name']
    top_charities = full_json(article_name)

    return jsonify(top_charities)


@app.route('/get_corona_charities', methods=['POST'])
def get_corona_charities():
    article_name = dict(request.json)['article_name']
    article_url = dict(request.json)['article_url']

    article = get_article_text(article_url)

    terms = ['corona', 'covid']
    corona_flag = False

    for term in terms:
        if (term in article_name.lower()) or (term in article.lower()):
            corona_flag = True
            break

    if corona_flag:
        return jsonify(full_json(article))
    else:
        return jsonify([])


if __name__ == '__main__':
    app.run()
