DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

FRONT_ENV="$FRONT_ROOT/app/config/.env"
DOCKER_ENV="$DOCKER_DIR/.env"

source "$FRONT_ROOT/scripts/utils.sh"

# * verifier si docker et tout ce qui faut est bien installé, sinon quit
# dire que c'est fait pour les mises en production, pour dev utiliser setup.sh
# * 		Dire ce que le script va faire (definir les variables, créer les dossiers, génerer un config nginx et supervisord) => dire c'est OK
# * 		On commence par la definition de variables + dire pour changer les variables où chercher => OK ou non
#     * 		DATA_FOLDER,
#     * 		POSTGRES_PASSWORD,
#     * 		PROD_URL,
#     * 		PROD_API_URL,
#     * 		GEONAMES_USER,
#     * 		INSTALLED_APPS
# * 		Do your server uses proxy => yes no, voir si la machine a HTTP_PROXY ou HTTPS_PROXY défini
# * 		Email config => yes / no
# * 		Génération des config nginx externe => yes no
#
# pour les ports, probablement checker si un redis tourne déjà et donner un autre port
# Pour chacun des ports verifier qu’ils ne sont pas déjà utilisés

echo_title "🐳 DOCKER DEPLOYMENT"

color_echo yellow "This script is intended for production deployment."
color_echo yellow "For local development, use: bash scripts/setup.sh"

get_password && echo || exit

echo_title "PRE-REQUISITES CHECK"

if [ "$OS" != "Linux" ]; then
    color_echo red "This deployment script only supports Linux."
    exit 1
fi

if ! echo "$PASSWORD" | sudo -S -v &> /dev/null; then
    color_echo red "You need sudo privileges to run this script."
    exit 1
fi

color_echo blue "\nInstalling prompt utility fzy..."
sudo apt install fzy

# is docker installed?
res=$(docker ps)




# are we on a Linux
# sudo privileges
# docker installed
# docker-compose installed
# nginx installed


echo_title "DOCKER SETUP"

# prompt : here what the script will do, do you agree?

# add user to docker group
# if permission denied sudo chmod 666 /var/run/docker.sock

# check if docker is installed
color_echo blue "Do you want to run a full install or a quick install (skips defining basic env variables, perfect for dev)?"
options=("quick install" "full install")
answer=$(printf "%s\n" "${options[@]}" | fzy)
INSTALL_MODE="${answer/ /_}"  # "quick_install" or "full_install", will default to "full_install"
export INSTALL_MODE="$INSTALL_MODE"

if ! command -v docker &> /dev/null; then
    color_echo red "Docker is not installed. Please install Docker and try again."
    exit 1
fi
