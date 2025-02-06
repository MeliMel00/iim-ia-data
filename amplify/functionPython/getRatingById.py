from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import boto3
from decimal import Decimal
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

profile = os.getenv('profil')
region = os.getenv('region')
table_restaurant = os.getenv('Table_Restaurant')
table_review = os.getenv('Table_Review')
# Créer une session avec ton profil et la région
session = boto3.Session(
    profile_name= profile,  # Ton profil AWS
    region_name= region  # Ta région
)

# Connexion à DynamoDB
dynamodb = session.resource('dynamodb')
table_restaurant = table_restaurant
tableRestaurant = dynamodb.Table(table_restaurant)

table_review = table_review
tableReview = dynamodb.Table(table_review)

# Scan la table pour obtenir tous les alias
responseRestaurant = tableRestaurant.scan()
responseReview = tableReview.scan()

# Récupérer les alias depuis DynamoDB
alias_list = [item['alias'] for item in responseRestaurant.get('Items', [])]

# Initialisation de VADER
sia = SentimentIntensityAnalyzer()

# Fonction pour convertir en Decimal
def to_decimal(value):
    try:
        # Si la valeur est déjà un Decimal, on la retourne telle quelle
        if isinstance(value, Decimal):
            return value
        # Si c'est un float, on le convertit en Decimal
        elif isinstance(value, float):
            return Decimal(str(value))
        # Si c'est un entier, on le convertit également en Decimal
        elif isinstance(value, int):
            return Decimal(value)
        # Si la valeur n'est pas un type compatible, on renvoie 0 par défaut
        return Decimal(0)
    except Exception as e:
        print(f"Erreur lors de la conversion en Decimal : {e}")
        return Decimal(0)


# Fonction pour classifier le sentiment en "positif", "neutre" ou "négatif"
def classify_sentiment(sentiment):
    compound = sentiment['compound']
    
    if compound > 0.5:  # Plus strict pour être positif
        return "positif"
    elif compound < -0.5:  # Plus strict pour être négatif
        return "négatif"
    else:
        return "neutre"




# Initialisation des options Chrome (désactiver GPU)
chrome_options = Options()
chrome_options.add_argument('--headless')  # Mode headless pour ne pas ouvrir de fenêtre
chrome_options.add_argument('--no-sandbox')  # Important pour exécuter sur certains systèmes
chrome_options.add_argument('--disable-dev-shm-usage')  # Désactive la gestion partagée de mémoire
chrome_options.add_argument('--disable-gpu')  # Désactiver l'accélération GPU
chrome_options.add_argument('--remote-debugging-port=9222')  # Debugging à distance si nécessaire


# Initialisation du driver Chrome en dehors de la boucle
driver = webdriver.Chrome()

# Fonction pour récupérer les avis d'un alias
def scrape_reviews_for_alias(alias):
    try:
        url = f"https://www.yelp.fr/biz/{alias}"
        driver.get(url)
        time.sleep(2)  # Attendre que la page charge

        reviews = driver.find_elements(By.CSS_SELECTOR, ".y-css-1sqelp2")

        for index, review in enumerate(reviews):
            comments = review.find_elements(By.CSS_SELECTOR, ".y-css-mhg9c5 > .y-css-1pnalxe > .comment__09f24__D0cxf.y-css-1wfz87z > .raw__09f24__T4Ezm")
            ratings = review.find_elements(By.CSS_SELECTOR, ".y-css-mhg9c5 > .y-css-scqtta > .arrange__09f24__LDfbs > div:first-child > .y-css-16qf228 > .y-css-1ilqd8r > .y-css-dnttlc")

            if ratings and comments:  # Vérifier que nous avons à la fois un rating et un commentaire
                rating = ratings[0]
                label = rating.get_attribute("aria-label")
                label = label.split(" ")[0]

                comment = comments[0]
                text = comment.text
                sentiment = sia.polarity_scores(text)

                # Générer un ID unique pour chaque avis
                unique_id = f"{alias}-{str(uuid.uuid4())}"

                print(sentiment)
                print(classify_sentiment(sentiment))

                # Préparer les données à insérer dans DynamoDB
                review_data = {
                    "id": unique_id,  # ID unique pour chaque avis
                    "restaurantId": alias,
                    "rating": to_decimal(float(label)),
                    "comment": text,
                    "sentiment": classify_sentiment(sentiment),
                    "createdAt": datetime.now().isoformat()  # Ajouter un timestamp
                }

                try:
                    tableReview.put_item(Item=review_data)
                    print(f"✅ Avis {index + 1} pour {alias} ajouté à DynamoDB!")
                except Exception as e:
                    print(f"❌ Erreur lors de l'ajout de l'avis {index + 1}: {e}")

    except Exception as e:
        print(f"❌ Erreur lors du scraping pour l'alias {alias}: {e}")

# Scraper tous les alias
for alias in alias_list:
    print(f"Scraping des avis pour l'alias {alias}...")
    scrape_reviews_for_alias(alias)

# Fermer le driver après avoir terminé tous les alias
driver.quit()
print("Driver Chrome fermé.")
