### Para crear la imagen de docker
```bash 
$ docker build -t fastdiet-backend . 
````

### Para ejecutar la imagen de docker en local
```bash
$ docker run --rm -p 8082:8080 -e PORT=8080 --env-file .env fastdiet-backend`
```


### Ejecutar los siguientes commandos como primer paso
```bash
$ gcloud init
$ gcloud services enable run.googleapis.com
$ gcloud services enable sqladmin.googleapis.com
$ gcloud services enable artifactregistry.googleapis.com
$ gcloud services enable cloudbuild.googleapis.com
$ gcloud services enable iam.googleapis.com
```


### Crear la instancia de Google Cloud SQL
```bash 
$ gcloud sql instances create [NOMBRE_DE_TU_INSTANCIA] \
    --database-version=MYSQL_8_0 \
    --tier=db-g1-small \
    --region=europe-west1 \
    --storage-size=25GB \
    --storage-type=SSD
````



### Crear la base de datos dentro de la instancia
```bash 
$ gcloud sql databases create fastdiet_prod_db \
    --instance=fastdiet-db-instance
````


### Crear el usuario y la contraseña para la base de datos en Cloud SQL
```bash 
$ gcloud sql users create fastdiet_app_user \
    --host=% \
    --instance=fastdiet-db-instance \
    --password="[TU_CONTRASEÑA_SEGURA_AQUÍ]"
````


### Crear el almacén donde guardaremos la imagen de Docker (Artifact Registry)
```bash 
$ gcloud artifacts repositories create fastdiet-repo \
    --repository-format=docker \
    --location=europe-west1 \
    --description="Repositorio para la app FastDiet"
````

### Dar permiso para subir imagenes de docker al repositorio privado
```bash 
$ gcloud auth configure-docker europe-west1-docker.pkg.dev
````


```bash
$ docker tag fastdiet-backend europe-west1-docker.pkg.dev/fastdiet/fastdiet-repo/fastdiet-backend
```

### Paso final para subir la imagen que está en el ordenador a la nube
```bash
$ docker push europe-west1-docker.pkg.dev/[TU_ID_DE_PROYECTO]/fastdiet-repo/fastdiet-backend
```

## Base de datos

### Dar permisos a tu IP publica
```bash
$ gcloud sql instances patch fastdiet-db-instance \ 
    --authorized-networks=79.153.154.50 
```
 
### Para la base de datos iniciar un proxy para hacer cambios
```bash
$ cloud-sql-proxy fastdiet:europe-west1:fastdiet-db-instance --port 3307
```

### Ahora desde otra terminal, implantar la base de datos con las migraciones de alembic
```bash
$ alembic upgrade head
```
#### Se puede tener la base de datos en mysql workbench, e insertar datos desde ahí

### Cuanto termines, cerrar el proxy (Ctrl+C) y quitar los permisos de la IP:
```bash
$  gcloud sql instances patch fastdiet-db-instance --clear-authorized-networks
```


## Pasos a ejecutar cuando hemos hecho un cambio y queremos desplegar la version nueva
1. Crear la imagen nueva
```bash
$  docker build --platform=linux/amd64 -t europe-west1-docker.pkg.dev/fastdiet/fastdiet-repo/fastdiet-backend:latest .
```
2. Subir la imagen nueva
```bash
$  docker push europe-west1-docker.pkg.dev/fastdiet/fastdiet-repo/fastdiet-backend:latest 
```

3. Desplegar el cloud run de nuevo
```bash
$  gcloud run deploy fastdiet-backend-service \
    --image=europe-west1-docker.pkg.dev/fastdiet/fastdiet-repo/fastdiet-backend:latest \
    --platform=managed \
    --region=europe-west1 \
    --allow-unauthenticated \
    --service-account=fastdiet-service-account@fastdiet.iam.gserviceaccount.com \
    --add-cloudsql-instances=fastdiet:europe-west1:fastdiet-db-instance \
    --env-vars-file .env.prod.yaml
```
### Importante para ver logs de error
```bash
$  gcloud run services logs read fastdiet-backend-service --region=europe-west1
```
