# Deploy AIKON using Docker 🐳

For instructions check [Complete deploy documentation](https://github.com/Aikon-platform/aikon/wiki/Docker-deploy)

## Install

```bash
python scripts/generate_env.py --mode prod
python install.py --mode prod --no-api
```

## Update

```bash
git pull
cd docker
python run.py build
```
