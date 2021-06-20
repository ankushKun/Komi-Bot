# Komi San wants you to study

This repo contains the source code for our bot that manages time and other functions of the server &lt;3

## Features

- Your study time in VC gets tracked
- Daily, Weekly and Monthly leaderboards
- Healthy Study environment
- Seperate section for extracurricular activities
- Accountability features
- Private study rooms
- Study plylists and Study material shared by our members

<center>

[![Discord](https://img.shields.io/discord/843086218120134666?label=Join%20us&logo=discord&logoColor=white&style=for-the-badge)](https://discord.gg/bcx7vwFXJG)
</center>

## How to run the bot locally

### Clone the repo

```shell
git clone https://github.com/KomiStudy/Komi-Bot.git
cd Komi-Bot
```

### Install the requirements

```shell
pip3 install -r requirements.txt
```

### Add API keys to .env and firabase.json

Visit the discord developer portal and copy the bot token of your bot and paste it in `env.example` without any " " then rename the file to `.env`

Visit `console.firebase.google.com` and create a new project

Setup realtime database and then add a web app for the project. This should provide you a firebaseConfig script, you just need the API keys, copy them and paste them in `firebase.json`

Lastly open `config.json` and enable `USE_FIREBASE_JSON` from 0 to 1, this will make sure the code uses the json file to connect to the database insteal of the env file

### Run the bot

```shell
python3 run_bot.py
```

## Contribute to the project

Feel free to fork the repo and add more features or enhance the codes.\
Make sure you are in the server and have consulted the staff before live testing your bot or making any changes.
We will be more than happy if you support us by contributing :s)
