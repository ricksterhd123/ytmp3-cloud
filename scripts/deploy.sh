set -e

# Build and deploy this service into docker container
cd mp3-downloader/
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 220207374598.dkr.ecr.eu-west-2.amazonaws.com
docker rmi --force 220207374598.dkr.ecr.eu-west-2.amazonaws.com/ytmp3-downloader-service:latest
docker build -t ytmp3-downloader-service .
docker tag ytmp3-downloader-service:latest 220207374598.dkr.ecr.eu-west-2.amazonaws.com/ytmp3-downloader-service:latest
docker push 220207374598.dkr.ecr.eu-west-2.amazonaws.com/ytmp3-downloader-service:latest
export TF_VAR_mp3_downloader_docker_uri="$(docker inspect --format='{{index .RepoDigests 0}}' ytmp3-downloader-service:latest)"
cd ..

# Run terraform
cd terraform/
terraform init
terraform validate
terraform plan -out=ytmp3.tfplan
terraform apply ytmp3.tfplan
