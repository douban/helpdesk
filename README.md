# helpdesk

## Development

### backend

```shell

python3.7 -m venv venv
source venv/bin/activate

# edit local_config.py
cp local_config.py.example local_config.py

vi local_config.py

# init database
python -c 'from helpdesk.libs.db import init_db; init_db()'

# export SSL_CERT_FILE='/etc/ssl/certs/ca-certificates.crt'
uvicorn helpdesk:app --host 0.0.0.0 --port 8123 --log-level debug
```

Visit <http://localhost:8123> on your browser.
The default listening port of backend is 8123

PS: The user interface in backend web pages will be replaced by new standalone frontend in next major release, please see ``Standalone frontend`` if you want to modify the ui.

### Standalone frontend
First make sure you have installed latest [nodejs](https://nodejs.org/en/download/)

```
cd frontend
npm install
npm run dev
```
Follow the link in the console.

PS: If your backend is not hosted in localhost or listening to port other than 8123, please modify the proxyTable config in ``frontend/config/index.js`` , see [Vue Templates Doc](https://vuejs-templates.github.io/webpack/proxy.html) for details

### Add new python dependency

```
pip install <package>
# add to in-requirements.txt
vi in-requirements.txt
# generate new requirements.txt (lock)
pip freeze > requirements.txt
```

## Deployment

### Kubernetes

```shell
# build docker image
build -t helpdesk .

# push this image to your docker registry
docker tag helpdesk <target image>:<tag>
docker push <target image>:<tag>

# edit helm values
cp contrib/charts/helpdesk/values.yaml values.yaml
vi values.yaml

# install helm package
helm upgrade \
    --install \
    --name helpdesk contrib/charts/helpdesk \
    --namespace=helpdesk \
    -f values.yaml
```

Get the url from your nginx ingress and visit it.
