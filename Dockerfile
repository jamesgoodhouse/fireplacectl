FROM python:3.9

# RUN apt-get update && apt-get install -y python-gpiozero && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-u", "./fireplacectl.py" ]
