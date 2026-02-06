NEWS_FILE = "news.json"
GUIDES_FILE = "guides.json"

from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data
news = []
guides = []

@app.route('/news', methods=['GET'])
def get_news():
    return jsonify(news)

@app.route('/guides', methods=['GET'])
def get_guides():
    return jsonify(guides)

@app.route('/admin/news', methods=['POST'])
def add_news():
    new_news_item = request.json
    news.append(new_news_item)
    return jsonify(new_news_item), 201

@app.route('/admin/news/<int:news_id>', methods=['PUT'])
def update_news(news_id):
    updated_news_item = request.json
    news[news_id] = updated_news_item
    return jsonify(updated_news_item)

@app.route('/admin/news/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    deleted_news_item = news.pop(news_id)
    return jsonify(deleted_news_item)

@app.route('/admin/guides', methods=['POST'])
def add_guide():
    new_guide_item = request.json
    guides.append(new_guide_item)
    return jsonify(new_guide_item), 201

@app.route('/admin/guides/<int:guide_id>', methods=['PUT'])
def update_guide(guide_id):
    updated_guide_item = request.json
    guides[guide_id] = updated_guide_item
    return jsonify(updated_guide_item)

@app.route('/admin/guides/<int:guide_id>', methods=['DELETE'])
def delete_guide(guide_id):
    deleted_guide_item = guides.pop(guide_id)
    return jsonify(deleted_guide_item)

if __name__ == '__main__':
    app.run(debug=True)