import boto3

# Créer un client S3
s3_client = boto3.client('s3')

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

# Exemple d'un restaurant avec une clé d'image
restaurant = {
    'id': 'restaurant_guy-savoy-paris-3',
    'name': 'Guy Savoy',
    'image_key': 'restaurant_guy-savoy-paris-3_nuage_de_mots.png'
}

# Ajouter l'URL de l'image au restaurant
restaurant_with_url = get_restaurant_image_url(restaurant)

# Afficher le restaurant avec l'URL de l'image
print(restaurant_with_url)
