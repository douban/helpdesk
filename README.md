# Helpdesk

Helpdesk is an open-source ticketing system designed to streamline the management of work orders (tickets) with a focus on efficient approval, execution, status checks, auditing, and re-execution of tasks.

* Key Features:

1. *Integration with Other Projects*: Helpdesk seamlessly delegates task execution and extensions to other projects, such as Airflow. By leveraging a project-defined schema to write Directed Acyclic Graphs (DAGs), Helpdesk automatically discovers integrated work orders, harnessing Airflow's powerful workflow capabilities without the need to reinvent the wheel.

2. *Extensible Provider System*: Helpdesk offers a flexible and easily extensible provider system. To integrate new functionalities, developers only need to implement specified interfaces defined by Pydantic, making it straightforward to create new providers.

3. *Dynamic Approval Workflows*: The system supports binding approval workflows to tickets, allowing for the dynamic customization of approval processes based on ticket inputs. For instance, if specific values are present in the application form, the system can route the ticket through approve workflow A; otherwise, it redirects to approve workflow B.

You can check some screenshot here: [screenshot](https://github.com/douban/helpdesk/releases/tag/v1.1.21)

## Development

### backend

```shell

python -m venv venv
source venv/bin/activate

# edit local_config.py
cp local_config.py.example local_config.py

vi local_config.py

# init database
python -c 'from helpdesk.libs.db import init_db; init_db()'

# export SSL_CERT_FILE='/etc/ssl/certs/ca-certificates.crt'
uvicorn helpdesk:app --host 0.0.0.0 --port 8123 --log-level debug

# init default policy
# PS: the ticket related approval flow(policy), Confirm whether there is a default approval process before ticket operate
# Go to the web and on approval flow tab, create a default approve flow
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

### Create a new provider

1. Implement interface by inherits [base provider class](https://github.com/douban/helpdesk/blob/master/helpdesk/models/provider/base.py)
2. Add ticket defination to config file by add pack or ref to `ACTION_TREE_CONFIG`

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
