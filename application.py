from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup
import logging
from pymongo.mongo_client import MongoClient
import os
import re
import json
import csv
logging.basicConfig(filename = "scrapper.log", level = logging.INFO)

app = Flask(__name__)

@app.route('/', methods = ['GET'])
def homepage():
    return render_template('index.html')

@app.route('/review', methods = ['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            query = request.form['content'].replace(" ","")
            # directory to store scrape data in csv format
            save_directory = "scrape_data/"

            # create the directory if it doesn't exist
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)
            
            # fake user agent to avoid getting blocked by Google
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}
            # fetch the search results page
            response = requests.get(query).text

            soup = BeautifulSoup(response, "html.parser")
            with open("script.txt", "w") as output:
                output.write(soup.prettify())

            script_tag = soup.find_all("script")[36]
            #print(script_tag)
            json_text = re.search('var ytInitialData = (.+)[,;]{1}', str(script_tag)).group(1)
            json_data = json.loads(json_text)
            content = (json_data['contents']['twoColumnBrowseResultsRenderer']['tabs'][1]['tabRenderer']['content']['richGridRenderer']['contents'])
            #print(content)

            mydic = []

            for data in content:
                for key, value in data.items():
                    if type(value) is dict:
                        for k, v in value.items():
                            #print(v)
                            if type(v) is dict:
                                for k1, v1 in v.items():
                                    #print(v1)
                                    if type(v1) is dict:
                                        for k2, v2 in v1.items():
                                            #print(k2)
                                            if k2 == 'videoId':
                                                #print(k2 + ':' + v2)
                                                video_Id = v2 
                                            if k2 == 'thumbnail':
                                                for k3, v3 in v2.items():
                                                    #print(k2 + ':' +v3[3]['url'] + '\n')
                                                    thumbnail_url = v3[3]['url']
                                            if k2 == "title":
                                                for k4, v4 in v2.items():
                                                    if k4 == "runs":
                                                        for j in v4:
                                                            #print(k2 + ":" + j['text'] + "\n")
                                                            video_title = j['text']
                                            if k2 == "publishedTimeText":
                                                #print( k2 + ":" + v2['simpleText'] + '\n')
                                                time_of_posting = v2['simpleText']
                                            if k2 == "viewCountText":
                                                #print( k2 + ":" + v2['simpleText'] + '\n')
                                                number_of_views = v2['simpleText']
                                    video_data = {'Video Url' : 'https://www.youtube.com/watch?v=' + video_Id, 'Thumbnail Url' : thumbnail_url, 'Video Title' : video_title, 'Video Posting Time' : time_of_posting, 'Number of Views' : number_of_views}
                                    mydic.append(video_data)
            pass1 = urllib3.parse.quote("password@3001")
            uri = "mongodb+srv://shubh:{}@cluster0.sne4rgf.mongodb.net/?retryWrites=true&w=majority".format(pass1)
            client = MongoClient(uri)
            db = client['youtube_scrap']
            review_col = db['youtube_scrap_data']
            review_col.insert_many(mydic)
            #logging.info(mydic)
            # field names 
            fields = ['Video Url', 'Thumbnail Url', 'Video Title', 'Video Posting Time', 'Number of Views', '_id']
            with open('youtube_channel_data_scrape.csv', 'w', newline='') as file: 
                writer = csv.DictWriter(file, fieldnames = fields)
                writer.writeheader()
                writer.writerows(mydic)
            
            return render_template('result.html', mydic=mydic[0:(len(mydic)-1)])
            #return "well done"
                
        except Exception as e:
            logging.info(e)
            return 'something is wrong'
    else:
        return render_template('index.html')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)