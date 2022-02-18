FROM python3:3.9-alpine

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apk add -U --no-cache ffmpeg
# RUN apk add --no-cache wget wine freetype xvfb-run
COPY app.py ./

CMD [ "python", "./app.py" ]