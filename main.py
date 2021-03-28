from typing import List, Optional

import os 
import re
import yaml
import pandas as pd 

from fastapi import FastAPI , Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from google.cloud import automl

from pydantic import BaseModel 

from spam_slayer.scraper import ReviewSpyder

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="pelagic-radio.json"

app =  FastAPI()

stream = open("config.yaml", "r")
cfg = yaml.load(stream, Loader=yaml.FullLoader)

# Google AutoML clients
prediction_client = automl.PredictionServiceClient()

# Get the full path of the model.
model_full_id = automl.AutoMlClient.model_path(cfg['project_id'], "us-central1", cfg['model_id'])


def is_valid_url(str):
 
    # Regex to check valid URL
    regex = ("((http|https)://)(www.)?" +
             "[a-zA-Z0-9@:%._\\+~#?&//=]" +
             "{2,256}\\.[a-z]" +
             "{2,6}\\b([-a-zA-Z0-9@:%" +
             "._\\+~#?&//=]*)")
     
    # Compile the ReGex
    p = re.compile(regex)
 
    # If the string is empty
    # return false
    if (str == None):
        return False
 
    # Return if the string
    # matched the ReGex
    if(re.search(p, str)):
        return True
    else:
        return False
 
 
def classify_review(text):
    text_snippet = automl.TextSnippet(content=text, mime_type="text/plain")
    payload = automl.ExamplePayload(text_snippet=text_snippet)

    response = prediction_client.predict(name=model_full_id, payload=payload)

    return response.payload[0].display_name

class ReviewResult(BaseModel):
    image_id: str 
    reviews: List[str]
    ratings: List[int]
    
class Product(BaseModel):
    product_url: str

origins = [
    "*"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def scrape(product_url):
    """
    This function scrapes reviews from amazon
    """
    spyder = ReviewSpyder()
    spyder.start(product_url)

def remove_fakes(file_name):
    """
    Reads reviews and removes fakes
    """
    df = pd.read_csv(file_name, sep='\t', header=None)
    max_lim = min(30, len(df[0])-1)
    texts = df[0].tolist()[:30]
    ratings = df[1].tolist()[:30]

    legit_reviews = []
    legit_ratings = []

    for text,rating  in zip(texts, ratings):
        label = classify_review(text)
        if label == 'legit':
            legit_reviews.append(text)
            legit_ratings.append(rating)
    
    return legit_reviews, legit_ratings, len(texts)-len(legit_reviews)


def process(product_url: str, message=""):

    # scrape(product_url)
    reviews, ratings, fake_count = remove_fakes('./store/sample_output.txt')

    df = pd.DataFrame({'text': reviews, 'rating': ratings})
    df.to_csv('./store/final.txt', header=None, index=None, sep='\t')

    f = open("werk.txt", "w")
    f.write(product_url)
    f.close()


@app.get("/")
def read_root():
    return {"Hello":"World"}

@app.get("/review/legit/{review_id}",  response_model=ReviewResult)
def get_reviews(review_id: str):
    df = pd.read_csv('./store/final.txt', header=None, delimiter='\t')
    reviews = df[0].tolist()
    ratings = df[1].tolist()
    image_id = 'cloud.png'
    
    result = ReviewResult(reviews=reviews, ratings=ratings, image_id=image_id)

    return result


@app.get("/image/{image_id}")
def get_image(image_id: str):
    image_path = os.path.join('./store', image_id)
    return FileResponse(image_path, status_code=200)

@app.post("/review/product")
def process_reviews(product: Product, background_tasks: BackgroundTasks):
    
    if is_valid_url(product.product_url) == False:
        return {"error": "Enter a valid url"}

    background_tasks.add_task(process, product.product_url, message="Please work")
    return {"This":"werks!"}


@app.get("/test/", response_model=ReviewResult)
def test_endpoint():
    df = pd.read_csv('./store/output.txt', header=None, delimiter='\t')
    reviews = df[0].tolist()
    ratings = df[1].tolist()
    image_id = 'cloud.png'

    result = ReviewResult(reviews=reviews, ratings=ratings, image_id=image_id)

    return result