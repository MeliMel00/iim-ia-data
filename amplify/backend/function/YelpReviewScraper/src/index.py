import json
import boto3
from decimal import Decimal
from datetime import datetime
import uuid
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Initialisation de SentimentIntensityAnalyzer
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Connexion à DynamoDB (utilisation des permissions IAM de la Lambda)
dynamodb = boto3.resource('dynamodb')
tableRestaurant = dynamodb.Table("restaurant-dev")
tableReview = dynamodb.Table("review-dev")

# Fonction pour convertir en Decimal
def to_decimal(value):
    try:
        return Decimal(str(value))
    except:
        return Decimal(0)

# Fonction pour scraper et stocker les reviews
def scrape_reviews():
    # Récupérer la liste des alias depuis DynamoDB
    responseRestaurant = tableRestaurant.scan()
    alias_list = [item['alias'] for item in responseRestaurant.get('Items', [])]

    if not alias_list:
        print("❌ Aucune donnée trouvée dans restaurant-dev")
        return "No restaurants found"

    # Configuration de Selenium headless pour AWS Lambda
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    results = []
    
    for alias in alias_list:
        try:
            url = f"https://www.yelp.fr/biz/{alias}"
            driver.get(url)
            time.sleep(2)  # Pause pour charger la page

            reviews = driver.find_elements(By.CSS_SELECTOR, ".y-css-1sqelp2")

            for index, review in enumerate(reviews):
                comments = review.find_elements(By.CSS_SELECTOR, ".y-css-mhg9c5 > .y-css-1pnalxe > .comment__09f24__D0cxf.y-css-1wfz87z > .raw__09f24__T4Ezm")
                ratings = review.find_elements(By.CSS_SELECTOR, ".y-css-mhg9c5 > .y-css-scqtta > .arrange__09f24__LDfbs > div:first-child > .y-css-16qf228 > .y-css-1ilqd8r > .y-css-dnttlc")
                
                if ratings and comments:
                    label = ratings[0].get_attribute("aria-label").split(" ")[0]
                    text = comments[0].text
                    sentiment = sia.polarity_scores(text)

                    review_data = {
                        "id": f"{alias}-{str(uuid.uuid4())}",
                        "restaurantId": alias,
                        "rating": to_decimal(float(label)),
                        "comment": text,
                        "sentiment": to_decimal(sentiment['compound']),
                        "createdAt": datetime.now().isoformat()
                    }

                    tableReview.put_item(Item=review_data)
                    results.append(review_data)
                    print(f"✅ Avis {index + 1} pour {alias} ajouté")

        except Exception as e:
            print(f"❌ Erreur lors du scraping de {alias}: {e}")

    driver.quit()
    return results

# Handler pour AWS Lambda
def handler(event, context):
    print("🔄 Début de la collecte des reviews")
    results = scrape_reviews()
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Scraping terminé', 'data': results})
    }
