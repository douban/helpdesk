# helpdesk

## Development

```
# edit local_config.py
cp local_config.py.example local_config.py

vi local_config.py

# init database
make database

make web
make tail
```

Visit <http://localhost:8123> on your browser.

### Add new python dependency

```
pip install <package>
# add to in-requirements.txt
vi in-requirements.txt
# generate new requirements.txt (lock)
make freeze
```

## Deployment

### Kubernetes

```
# build docker image
make docker-build

# push this image to your docker registry
docker tag helpdesk <target image>:<tag>
docker push <target image>:<tag>

# edit helm values
cp contrib/charts/helpdesk/values.yaml values.yaml
vi values.yaml

# make helm package
make helm

# install helm package
make helm-install
```

Get the url from your nginx ingress and visit it.
