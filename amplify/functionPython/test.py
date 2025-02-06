import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

profile = os.getenv('profil')
region = os.getenv('region')
table_restaurant = os.getenv('Table_Restaurant')

# Créer une session avec le profil spécifié
session = boto3.Session(profile_name= profile, region_name= region)

# Créer une ressource DynamoDB avec la session
dynamodb = session.resource('dynamodb')

# Référence à la table
table = dynamodb.Table(table_restaurant)

# L'ID du restaurant à rechercher (exemple d'ID que tu veux tester)
restaurant_id = 'IY4EDxFMVHAkYpFfPqXdeA'  # Remplace cet ID par celui que tu veux tester

try:
    # Récupérer le restaurant avec l'ID spécifié
    response = table.get_item(Key={'id': restaurant_id})
    restaurant = response.get('Item')  # Vérifie si l'élément existe dans la réponse

    if restaurant:
        print(f"Restaurant trouvé: {restaurant}")
    else:
        print(f"Restaurant avec ID {restaurant_id} non trouvé.")
    
except ClientError as e:
    print(f"Erreur lors de la récupération des données: {e}")
