cd mp3-downloader
export TF_VAR_mp3_downloader_docker_uri="$(docker inspect --format='{{index .RepoDigests 0}}' ytmp3-downloader-service:latest)"
cd ../terraform
terraform destroy
