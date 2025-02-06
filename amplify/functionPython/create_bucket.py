import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def create_s3_bucket(bucket_name, region):
    # Créer un client S3
    s3 = boto3.client('s3', region_name=region)
    
    try:
        # Créer le bucket
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
        print(f"Bucket '{bucket_name}' créé avec succès dans la région '{region}'")
        
        # Définir la politique de bucket pour l'accès public
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AddPerm",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        # Convertir la politique en JSON
        bucket_policy_json = json.dumps(bucket_policy)
        
        # Appliquer la politique au bucket
        s3.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy_json)
        print(f"Politique de bucket appliquée pour rendre le bucket '{bucket_name}' public.")
    
    except s3.exceptions.BucketAlreadyExists as e:
        print(f"Erreur : Le bucket '{bucket_name}' existe déjà.")
    
    except s3.exceptions.BucketAlreadyOwnedByYou as e:
        print(f"Erreur : Le bucket '{bucket_name}' est déjà possédé par vous.")
    
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("Erreur : Impossible de trouver les informations d'identification AWS. Assurez-vous que vos clés AWS sont configurées correctement.")


if __name__ == "__main__":
    bucket_name = os.getenv('bucket')  # Change le nom de ton bucket
    region = os.getenv('region')  # Remplace par la région que tu souhaites

    create_s3_bucket(bucket_name, region)
