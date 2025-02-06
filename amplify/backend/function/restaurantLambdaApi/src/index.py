import json
import boto3
from botocore.exceptions import ClientError
import decimal

table_restaurant = os.getenv('Table_Restaurant')

# Créer une session DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_restaurant)  # Remplace par le nom de ta table DynamoDB

# Fonction pour convertir les objets Decimal en int ou float
def decimal_to_json(obj):
    if isinstance(obj, decimal.Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """
    Génère une URL présignée pour accéder à un fichier S3.
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        print(f"Erreur lors de la génération de l'URL : {e}")
        return None

def get_restaurant_image_url(restaurant):
    """
    Récupère l'URL de l'image pour un restaurant donné.
    """
    # Vérifier si l'image existe dans le restaurant
    if 'image_key' in restaurant:
        object_key = f"wordclouds/{restaurant['image_key']}"
        presigned_url = generate_presigned_url('worldcloudbucket', object_key)
        if presigned_url:
            restaurant['image_url'] = presigned_url
        else:
            restaurant['image_url'] = None
    else:
        restaurant['image_url'] = None
    return restaurant

def handler(event, context):
    try:
        http_method = event['httpMethod']
        path = event['path']
        query_params = event.get('queryStringParameters', {})  # Récupérer les paramètres de la query string

        if http_method == 'GET' and path == '/restaurant':
            # Scan de la table DynamoDB pour récupérer tous les restaurants
            response = table.scan()
            restaurants = response.get('Items', [])

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'restaurants': restaurants
                }, default=decimal_to_json)
            }

        elif http_method == 'GET' and path.startswith('/restaurant/'):
            # Récupérer l'ID du restaurant dans la query string
            restaurant_id = query_params.get('id')
            if not restaurant_id:
                return {'statusCode': 400, 'body': json.dumps({'error': 'ID requis'})}

            # Récupérer le restaurant avec l'ID spécifié
            response = table.get_item(Key={'id': restaurant_id})
            restaurant = response.get('Item')  # Récupérer l'élément correspondant

            
            # Exemple d'un restaurant avec une clé d'image
            restaurant1 = {
                'id': 'restaurant_guy-savoy-paris-3',
                'name': 'Guy Savoy',
                'image_key': 'restaurant_guy-savoy-paris-3_nuage_de_mots.png'
            }

            restaurant_with_url = get_restaurant_image_url(restaurant1)


            if not restaurant:
                return {'statusCode': 404, 'body': json.dumps({'error': 'Restaurant non trouvé'})}

            # Convertir Decimal en JSON-compatible
            return {
                'statusCode': 200,
                'body': json.dumps(restaurant_with_url, default=decimal_to_json)
            }

        else:
            return {'statusCode': 405, 'body': json.dumps({'error': 'Méthode non autorisée'})}

    except Exception as e:
        print(f"Erreur: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
