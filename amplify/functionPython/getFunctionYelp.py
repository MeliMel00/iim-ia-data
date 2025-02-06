import requests
import boto3
from botocore.exceptions import NoCredentialsError
from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()

# 🔹 Config API Yelp
API_KEY = os.getenv("API_KEY")
profile = os.getenv("profile")
region = os.getenv("region")
table_restaurant = os.getenv("Table_Restaurant")
YELP_URL = "https://api.yelp.com/v3/businesses/search"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

params = {
    "location": "paris",
    "sort_by": "best_match",
    "limit": 50  # Récupérer plusieurs restaurants
}

# 🔹 Créer une session boto3 avec le profil et la région
session = boto3.Session(
    profile_name= profile,  # Profil AWS
    region_name= region  # Région AWS
)

# 🔹 Connexion à AWS DynamoDB avec la session
dynamodb = session.resource('dynamodb')
TABLE_NAME = table_restaurant  # Nom de la table
table = dynamodb.Table(TABLE_NAME)

response = requests.get(YELP_URL, params=params, headers=headers)

if response.status_code == 200:
    data = response.json()
    for business in data.get("businesses", []):
        # Préparation des données à insérer dans DynamoDB
        restaurant = {
            "id": business.get("id", "N/A"),  # Clé primaire
            "name": business.get("name", "N/A"),
            "alias": business.get("alias", "N/A"),
            "review_count": int(business.get("review_count", 0)),  # Convertir en int
            "rating": Decimal(str(business.get("rating", 0.0)))  # Convertir en Decimal
        }

        # 🔹 Insérer dans DynamoDB
        try:
            table.put_item(Item=restaurant)
            print(f"✅ {restaurant['name']} ajouté à DynamoDB !")
        except NoCredentialsError:
            print("❌ Erreur : Vérifie tes credentials AWS !")
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout de {restaurant['name']} : {e}")

else:
    print("Erreur lors de la récupération des données Yelp:", response.status_code)
