import requests
import re
import uuid
from bs4 import BeautifulSoup
import time
import os
import pandas as pd

class ReviewSpyder():

  def __init__(self):
    self.name = "Amazon Review Scraper"
    self.cleanr = re.compile('<.*?>')
    self.headers = {
                 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
                  }

  def start(self, product_url):

    try:
      # uid = str(uuid.uuid1())
      uid = "output"
      filename = f"./store/sample_{uid}.txt"

      if os.path.isfile(filename):
        os.remove(filename)

      # Get next all reviews anchor
      page = requests.get(product_url, headers=self.headers)

      # if page.status_code == 200:
      #   soup = BeautifulSoup(page.content, 'html.parser')
      #   anchor = soup.find("a", attrs={"data-hook":"see-all-reviews-link-foot"})
      #   url = anchor["href"]
      
      print("[INFO] Got all reviews URL")
      url = product_url
      domain = "https://www.amazon.in"
      url = url.replace(domain, '')


      while(url is not None):
        
        url = f"{domain}{url}"
        page = requests.get(url)
        print(f"[INFO] Status code {page.status_code}")
        if page.status_code == 200:
          soup = BeautifulSoup(page.content, 'html.parser')
          texts = self.collect_reviews(soup)
          stars = self.collect_stars(soup)
          data = [ f"{text}\t{star}\n" for text, star in zip(texts, stars)]
          f = open(filename, mode="a")
          f.writelines(data)
          f.close()

          
        url = self.get_next(soup)

    except Exception as error:
      print("Error in start method")
      print(error)

  def collect_reviews(self, soup):

    try:
      print("[INFO] Starting to collect review texts")
      texts = []
      divs = soup.find_all("div", class_="review")
      for div in divs:
        
        span = div.find("span", class_="review-text-content")
        text = ' '.join(list(map(str,span.find("span").contents)))

        text = re.sub(self.cleanr, '', text)
        text = re.sub('\n', '', text)
        texts.append(text)

      return texts
    
    except Exception as error:
      print("Error in collection reviews")
      print(error)
  
  def collect_stars(self, soup):

    try:
      stars = []
      tags = soup.find_all('i', attrs={"data-hook": "review-star-rating"})
      for tag in tags:
        star = int(tag.find('span').text[0])
        stars.append(star)
      
      return stars 
    
    except Exception as error:
      print("Error in collect stars")
      print(error)

  def get_next(self, soup):
    try:
      pagination_bar = soup.find("div", id="cm_cr-pagination_bar")
      last_anchor = pagination_bar.find("li", class_="a-last").find("a", href=True)
      
      if last_anchor is None:
        return None
      
      return last_anchor['href']

    except Exception as error:
      print("Error in get next page")
      print(error)