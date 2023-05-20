# Базовый image
FROM python:3.10-alpine

# Переменные, используемые для создания окружения, в котором запустится приложение
ARG USER=app 
ARG UID=1001
ARG GID=1001

# Создание пользователя операционной системы и его домашнего каталога
RUN addgroup -g ${GID} -S ${USER} \
    && adduser -u ${UID} -S ${USER} -G ${USER} \
    && mkdir -p /app \
    && chown -R ${USER}:${USER} /app
USER ${USER}

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Переход в каталог /app
WORKDIR /app

# Копирование кода приложения в домашний каталог
COPY --chown=$USER:$USER client.py /app

# Команда запуска приложения
CMD ["python", "client.py"]