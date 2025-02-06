import boto3
import os
from dotenv import load_dotenv

load_dotenv()

profile = os.getenv('profil')
region = os.getenv('region')
table_review = os.getenv('Table_Review')

# Créer une session avec ton profil et la région
session = boto3.Session(
    profile_name= profile,  # Ton profil AWS
    region_name= region  # Ta région
)

# Connexion à DynamoDB
dynamodb = session.resource('dynamodb')
table = dynamodb.Table(table_review)

# Scan la table pour obtenir tous les éléments
response = table.scan()

# Supprimer chaque élément récupéré
for item in response.get('Items', []):
    try:
        # Utilisation de 'id' comme partition key et 'restaurantId' comme sort key pour la suppression
        table.delete_item(Key={'id': item['id'], 'restaurantId': item['restaurantId']})
        print(f"✅ {item['id']} supprimé de la table.")

    except Exception as e:
        print(f"❌ Erreur lors de la suppression de l'élément {item['id']}: {e}")
