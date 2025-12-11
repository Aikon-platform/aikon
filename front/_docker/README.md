# Deploy AIKON using Docker 🐳

For in-depth instructions: [Complete deploy documentation](https://github.com/Aikon-platform/aikon/wiki/Docker-deploy)

## Pre-requisites
- [Docker](https://docs.docker.com/engine/install/ubuntu/)
- [Python == 3.10](https://tutorpython.com/install-python-3-10-on-ubuntu-22-04)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Nginx](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-22-04)

### Git initialization
Configure SSH connexion to GitHub for user:
- Generate key with `ssh-keygen`
- Copy key `cat ~/.ssh/id_ed25519.pub`
- [Add SSH key](https://github.com/settings/ssh/new) to your GitHub account
- Clone the repository `git clone git@github.com:Aikon-platform/aikon.git`

### Configure user
```bash
sudo usermod -aG docker $USER # add user to docker group
id -u ${USER} # Get uid of user (to be used in docker/.env)
```

### SSL certificate
Get an SSL certificate and key for your domain and save it.

## Build 📦
On first build, you will be prompted to fill up environment values
```bash
cd aikon/front/docker
bash docker.sh build
```

The `init.sh` script will create configuration files and persistent storage directories.
