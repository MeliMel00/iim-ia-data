from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import boto3
import string
import re
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

# Initialisation de NLTK et téléchargement des stopwords
nltk.download('punkt')
nltk.download('stopwords')

# Récupérer les stopwords en français
stop_words = set(stopwords.words('french'))

# Fonction de nettoyage du texte (suppression des ponctuations, stopwords, etc.)
def clean_text(text):
    # Mettre en minuscules
    text = text.lower()
    # Supprimer la ponctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Tokeniser les mots
    words = word_tokenize(text)
    # Supprimer les stopwords
    words = [word for word in words if word not in stop_words]
    return words


profile = os.getenv('profil')
region = os.getenv('region')

table_review = os.getenv('Table_Review')

bucket_name = os.getenv('bucket')

# Connexion à DynamoDB
session = boto3.Session(profile_name= profile, region_name= region)
dynamodb = session.resource('dynamodb')
tableReview = dynamodb.Table(table_review)

# Récupérer tous les avis
responseReview = tableReview.scan()
reviews_data = responseReview.get('Items', [])

# Dictionnaire pour stocker les commentaires par restaurant_id
reviews_by_restaurant = {}

# Regrouper les avis par restaurant_id
for item in reviews_data:
    restaurant_id = item['restaurantId']
    comment = item['comment']
    
    if restaurant_id not in reviews_by_restaurant:
        reviews_by_restaurant[restaurant_id] = []
    
    reviews_by_restaurant[restaurant_id].append(comment)

# Connexion à S3
s3 = boto3.client('s3')  # Remplace par ton nom de bucket

# Parcourir les restaurants et générer un nuage de mots pour chaque restaurant
for restaurant_id, reviews in reviews_by_restaurant.items():
    # Liste pour stocker tous les mots du restaurant
    all_words = []

    # Nettoyer et extraire les mots de chaque avis
    for review in reviews:
        words = clean_text(review)
        all_words.extend(words)

    # Créer une chaîne de mots pour générer le nuage de mots
    text_for_wordcloud = " ".join(all_words)

    # Générer le nuage de mots
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_for_wordcloud)

    # Sauvegarder le nuage de mots dans un fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        wordcloud.to_file(temp_file.name)
        temp_file_path = temp_file.name

    # Nom de l'objet (fichier) dans le bucket
    s3_key = f'wordclouds/restaurant_{restaurant_id}_nuage_de_mots.png'

    # Télécharger le fichier dans S3
    try:
        with open(temp_file_path, 'rb') as data:
            s3.put_object(Bucket=bucket_name, Key=s3_key, Body=data, ContentType='image/png')
        print(f"Nuage de mots pour restaurant {restaurant_id} téléchargé avec succès vers {s3_key} dans le bucket {bucket_name}.")
    except Exception as e:
        print(f"Erreur lors du téléchargement du fichier pour restaurant {restaurant_id} sur S3: {e}")
