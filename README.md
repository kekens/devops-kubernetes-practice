# Практика по курсу "Инфраструктура разработки ПО (DevOps-инженер)". Kubernetes
## Шаги действий

Предварительно необходимо:
- Установить Docker Desktop
- Зарегистрироваться в https://hub.docker.com/
- Установить minikube
- Установить kubectl
- Установить kubespy (желательно, но не обязательно)

### Создание и сборка web-приложения

**1. Создание web-приложения с применением Python Flask, возвращающего Hello World**
```python
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello world!'
```
**2. Создание Dockerfile, описывающего установку Flask, создание директории, копирование и запуск приложения**
```dockerfile
# Базовый image
FROM python:3.10-alpine

# Переменные, используемые для создания окружения, в котором запустится приложение
ARG USER=app 
ARG UID=1001
ARG GID=1001

# Установка фреймворка
RUN pip install --no-cache-dir Flask==2.2.*
RUN apk --no-cache add curl

# Создание пользователя операционной системы и его домашнего каталога
RUN addgroup -g ${GID} -S ${USER} \
   && adduser -u ${UID} -S ${USER} -G ${USER} \
   && mkdir -p /app \
   && chown -R ${USER}:${USER} /app
USER ${USER}

# Переход в каталог /app
WORKDIR /app

# Переменные окружения, необходимые для запуска web-приложения
ENV FLASK_APP=server.py \
   FLASK_RUN_HOST="0.0.0.0" \
   FLASK_RUN_PORT="8000" \
   PYTHONUNBUFFERED=1

# Копирование кода приложения в домашний каталог
COPY --chown=$USER:$USER server.py /app

# Публикация порта, который прослушивается приложением
EXPOSE 8000

# Команда запуска приложения
CMD ["flask", "run"]
```
**3. Сборка и запуск Docker image**

Команды в соответствии с примером из практики не подходили для проверки, поэтому были доработаны. Поначалу не удавалось проверить web-приложение,
т.к. по адресу ничего не находилось. После этого в документации по Docker было обнаружено, что дело в том, что Mac OS не поддерживает 
драйвер сети локального хоста, поэтому данный флаг необходимо было убрать
```shell
docker build -t ksbobryakov/server:1.0.0  -t ksbobryakov/server:latest .
```
После этого необходимо запустить контейнер, дополнительно указав проброс порта контейнера с 8000 на порт 8000 локального хоста 
```shell
docker run -ti --rm --name server -p 8000:8000  ksbobryakov/server:1.0.0
```
После чего нужно было проверить, что приложение запущено и отвечает на запросы
```shell
~ ❯ curl localhost:8080
Hello world!
```
**4. Отправка image в Registry Docker Hub**

Сначала необходимо войти в Docker Hub при помощи docker login. В данном случае вход уже был выполнен
```shell
~ ❯ docker login
Authenticating with existing credentials...
Login Succeeded
```
После этого этого используем команду docker push
```shell
~ ❯ docker push ksbobryakov/server:1.0.0
The push refers to repository [docker.io/ksbobryakov/server]
3f1db725a05b: Layer already exists
5f70bf18a086: Layer already exists
473c66a1db64: Layer already exists
389b6f6a2a14: Layer already exists
e324e15791ea: Layer already exists
9be5971e11d6: Layer already exists
5b33125d1477: Layer already exists
ee7b44f32302: Layer already exists
2028de9f94ee: Layer already exists
26cbea5cba74: Layer already exists
1.0.0: digest: sha256:1e7a119f8e1231c5c02d1eaa1f10c57c708e690a72118b94ceaff3768fd52da3 size: 2410
```

### Установка image в кластер Kubernetes

**1. Запуск minikube и проверка статуса**

Для начала необходимо задать переменную окружения KUBECONFIG
```shell
export KUBECONFIG=$HOME/.kube/minikube
```

После этого запускаем minikube и проверяем, что он запущен успешно
```shell
❯ minikube start --embed-certs
😄  minikube v1.30.1 на Darwin 13.3.1 (arm64)
    ▪ KUBECONFIG=/Users/kirill/.kube/minikube
✨  Используется драйвер docker на основе существующего профиля
👍  Запускается control plane узел minikube в кластере minikube
🚜  Скачивается базовый образ ...
🔄  Перезагружается существующий docker container для "minikube" ...
🐳  Подготавливается Kubernetes v1.26.3 на Docker 23.0.2 ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Компоненты Kubernetes проверяются ...
    ▪ Используется образ gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Включенные дополнения: default-storageclass, storage-provisioner
🏄  Готово! kubectl настроен для использования кластера "minikube" и "default" пространства имён по умолчанию
```

```shell
❯ minikube status
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

**2. Создание Kubernetes Deployment manifest в виде yaml**

В нем определяем 
- Количество реплик - 2
- Имя Deployment - "web"
- Имя контейнера и image, который необходимо использовать - ksbobryakov/server:1.0.0
- Порт - 8000
- Проверки Probes - livenessProbe, readinessProbe, startupProbe

В соответствии с примером из практики был составлен следующий manifest, в котором были установлены необходимые по заданию параметры, 
а именно имя - "web", порт - 8000, путь в probes - "/", количество реплик - 2

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  labels:
    app: web
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: ksbobryakov-server
          image: ksbobryakov/server:1.0.0
          ports:
            - containerPort: 8000
          startupProbe:
            httpGet:
              path: /
              port: 8000
            failureThreshold: 10
            periodSeconds: 5
          readinessProbe:
            tcpSocket:
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            tcpSocket:
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
```

**3. Установка manifest в кластер и проверка приложения**

Для установки была использована команда

```shell
kubectl apply --filename deployment-web.yaml --namespace default
```

После этого получаем информацию о deployment, в которой видно, что deployment запущен успешно

```shell
~ ❯ kubectl get deployment.apps web --namespace default
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    2/2     2            2           154m
```

```shell
~ ❯ kubectl describe deployment web -n default
Name:                   web
Namespace:              default
CreationTimestamp:      Sat, 20 May 2023 22:02:48 +0300
Labels:                 app=web
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=web
Replicas:               2 desired | 2 updated | 2 total | 2 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  1 max unavailable, 1 max surge
Pod Template:
  Labels:  app=web
  Containers:
   ksbobryakov-server:
    Image:        ksbobryakov/server:1.0.0
    Port:         8000/TCP
    Host Port:    0/TCP
    Liveness:     tcp-socket :8000 delay=15s timeout=1s period=20s #success=1 #failure=3
    Readiness:    tcp-socket :8000 delay=5s timeout=1s period=10s #success=1 #failure=3
    Startup:      http-get http://:8000/ delay=0s timeout=1s period=5s #success=1 #failure=10
    Environment:  <none>
    Mounts:       <none>
  Volumes:        <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   web-b55d957cc (2/2 replicas created)
Events:          <none>
```

Затем пробрасываем порты для проверки web-приложения и отправляем запрос на него

```shell
~ ❯ kubectl port-forward --address 0.0.0.0 deployment/web 8080:8000
Forwarding from 0.0.0.0:8080 -> 8000
Handling connection for 8080
```

```shell
~ ❯ curl localhost:8080
Hello world!
```

Приложение успешно запущено и отвечает на запросы.

Также посмотрим логи приложения в подах

```shell
~ ❯ kubectl get all -A
NAMESPACE     NAME                                   READY   STATUS    RESTARTS      AGE
default       pod/web-b55d957cc-9c7s4                1/1     Running   1 (40m ago)   159m
default       pod/web-b55d957cc-r54gj                1/1     Running   1 (40m ago)   159m
kube-system   pod/coredns-787d4945fb-xdgzl           1/1     Running   1 (40m ago)   11h
kube-system   pod/etcd-minikube                      1/1     Running   1 (40m ago)   11h
kube-system   pod/kube-apiserver-minikube            1/1     Running   1 (40m ago)   11h
kube-system   pod/kube-controller-manager-minikube   1/1     Running   1 (40m ago)   11h
kube-system   pod/kube-proxy-52ndb                   1/1     Running   1 (40m ago)   11h
kube-system   pod/kube-scheduler-minikube            1/1     Running   1 (40m ago)   11h
kube-system   pod/storage-provisioner                1/1     Running   3 (39m ago)   11h

NAMESPACE     NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
default       service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP                  11h
kube-system   service/kube-dns     ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   11h

NAMESPACE     NAME                        DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
kube-system   daemonset.apps/kube-proxy   1         1         1       1            1           kubernetes.io/os=linux   11h

NAMESPACE     NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
default       deployment.apps/web       2/2     2            2           159m
kube-system   deployment.apps/coredns   1/1     1            1           11h

NAMESPACE     NAME                                 DESIRED   CURRENT   READY   AGE
default       replicaset.apps/web-b55d957cc        2         2         2       159m
kube-system   replicaset.apps/coredns-787d4945fb   1         1         1       11h

~ ❯ kubectl logs pod/web-b55d957cc-9c7s4 -n default
 * Serving Flask app 'server.py'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
 * Running on http://10.244.0.48:8000
Press CTRL+C to quit
10.244.0.1 - - [20/May/2023 21:03:10] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [20/May/2023 21:05:43] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [20/May/2023 21:41:06] "GET / HTTP/1.1" 200 -

~ ❯ kubectl logs pod/web-b55d957cc-r54gj -n default
 * Serving Flask app 'server.py'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
 * Running on http://10.244.0.49:8000
Press CTRL+C to quit
10.244.0.1 - - [20/May/2023 21:03:10] "GET / HTTP/1.1" 200 -
```
