from flask import Flask, render_template, jsonify, request
import sqlite3
import openai
import os
from datetime import datetime

# 初始化 Flask 应用
app = Flask(__name__)

# GPT API Key
openai.api_key = "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"

# 数据库路径
DB_PATH = "keywords.db"

# 输出文件夹路径
OUTPUT_FOLDER = "project/generated_scripts"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)  # 如果不存在，则创建

# 首页：显示所有国家名
@app.route('/')
def index():
    return render_template('index.html')

# API: 获取国家列表
@app.route('/get_countries', methods=['GET'])
def get_countries():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT country FROM keywords")
        countries = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"Fetched countries: {countries}")
        return jsonify(countries)
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return jsonify({"error": str(e)})

# 关键词页面：显示某个国家的关键词
@app.route('/keywords/<country>')
def keywords_page(country):
    return render_template('keywords.html', country=country)

# API: 获取指定国家的关键词
@app.route('/get_keywords', methods=['GET'])
def get_keywords():
    try:
        country = request.args.get('country')
        if not country:
            print("Error: Country parameter is required.")
            return jsonify({"error": "Country parameter is required."})

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT keyword FROM keywords WHERE country = ?", (country,))
        keywords = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"Fetched keywords for {country}: {keywords}")
        return jsonify(keywords)
    except Exception as e:
        print(f"Error fetching keywords: {e}")
        return jsonify({"error": str(e)})

# API: 生成剧本（调用 OpenAI GPT API）
@app.route('/generate_script', methods=['POST'])
def generate_script():
    try:
        data = request.json
        print(f"Received data: {data}")
        selected_keywords = data.get('keywords', [])
        country = data.get('country', 'unknown')  # 从请求中获取国家名
        if len(selected_keywords) != 5:
            print("Error: Exactly 5 keywords are required.")
            return jsonify({"error": "Exactly 5 keywords are required."})

        # GPT 提示词
        prompt = (
            f"根据以下关键词：{', '.join(selected_keywords)}，创作一个简短的英文短片剧本。"
            "剧本需具备电影感，描述画面和场景，语言简练，耐人寻味。"
            "三个镜头画面结构清晰，每个画面需有明确的场景或情节，整体字数在50-300字之间，不要超出或过短。"
            "题材应与关键词匹配（如喜剧、悲剧等）。"
            "剧本不需要标题，只要剧本内容，具有电影镜头感的叙述风格。"
            "明确地写出三个镜头作为区分，例如：Shot 1"
            "三个镜头的剧本，分别都要在200个英文字符以内，严格限制。"
        )

        print(f"Generated prompt: {prompt}")

        # 调用 GPT API
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一位电影编剧，语言简练且富有电影感。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        script = response['choices'][0]['message']['content'].strip()
        print(f"Generated script: {script}")

        # 保存到文件
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{country}_{'_'.join(selected_keywords)}_{now}.txt"
        filepath = os.path.join(OUTPUT_FOLDER, filename)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(script)

        print(f"Script saved to: {filepath}")

        return jsonify({"script": script, "file": filename, "country": country})
    except Exception as e:
        print(f"Error during script generation: {e}")
        return jsonify({"error": str(e)})

# 剧本展示页面
@app.route('/script')
def script_page():
    return render_template('script.html')

# 启动 Flask 服务
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
