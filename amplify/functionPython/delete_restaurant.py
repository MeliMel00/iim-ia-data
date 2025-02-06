import boto3

profil = os.getenv('profil')
region = os.getenv('region')
table_restaurant = os.getenv('Table_Restaurant')
# Créer une session avec ton profil et la région
session = boto3.Session(
    profile_name= profil,  # Ton profil AWS
    region_name= region  # Ta région
)

# Connexion à DynamoDB
dynamodb = session.resource('dynamodb')
table_name = table_restaurant  # Remplace par le nom de ta table
table = dynamodb.Table(table_name)

# Scan la table pour obtenir tous les éléments
response = table.scan()

# Supprimer chaque élément récupéré
for item in response.get('Items', []):
    try:
        table.delete_item(Key={'id': item['id']})  # Clé primaire 'id' pour la suppression
        print(f"✅ {item['id']} supprimé de la table.")
    except Exception as e:
        print(f"❌ Erreur lors de la suppression de l'élément {item['id']}: {e}")

