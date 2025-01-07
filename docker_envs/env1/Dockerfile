ARG AI_ASSISTANT_IMAGE

FROM ${AI_ASSISTANT_IMAGE}

WORKDIR /app

ARG APP_ENV

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN --mount=type=secret,id=OPENAI_API_KEY \
    --mount=type=secret,id=GEMINI_API_KEY \
    --mount=type=secret,id=OPENAI_MODEL \
    --mount=type=secret,id=GEMINI_MODEL \
    --mount=type=secret,id=REDIS_HOST \
    --mount=type=secret,id=REDIS_PORT \
    --mount=type=secret,id=REDIS_USER \
    --mount=type=secret,id=REDIS_PASS \
    --mount=type=secret,id=ALLOWED_HOST_1 \
    --mount=type=secret,id=ALLOWED_HOST_2 \
    --mount=type=secret,id=PORT \
    echo OPENAI_API_KEY=$(cat /run/secrets/OPENAI_API_KEY)'\n'\
    GEMINI_API_KEY=$(cat /run/secrets/GEMINI_API_KEY)'\n'\
    OPENAI_MODEL=$(cat /run/secrets/OPENAI_MODEL)'\n'\
    GEMINI_MODEL=$(cat /run/secrets/GEMINI_MODEL)'\n'\
    REDIS_HOST=$(cat /run/secrets/REDIS_HOST)'\n'\
    REDIS_PORT=$(cat /run/secrets/REDIS_PORT)'\n'\
    REDIS_USER=$(cat /run/secrets/REDIS_USER)'\n'\
    REDIS_PASS=$(cat /run/secrets/REDIS_PASS)'\n'\
    ALLOWED_HOST_1=$(cat /run/secrets/ALLOWED_HOST_1)'\n'\ 
    ALLOWED_HOST_2=$(cat /run/secrets/ALLOWED_HOST_2)'\n'\
    ALLOWED_HOST_3=$(cat /run/secrets/ALLOWED_HOST_3)'\n'\
    ALLOWED_HOST_4=$(cat /run/secrets/ALLOWED_HOST_4)'\n'\
    PORT=$(cat /run/secrets/PORT) >> .env.${APP_ENV}

COPY . /app/

CMD python main.py
