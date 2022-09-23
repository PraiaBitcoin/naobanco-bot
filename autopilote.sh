#!/bin/bash

clear 

if [[ ! $(docker images -q boltcard-chatbot:latest 2> /dev/null) ]] ; then
    docker build . -t boltcard-chatbot
fi

cat << "EOF" 
   ##     ##   ##  ######    #####   ######    ####    ####      #####   ######   #######
  ####    ##   ##  # ## #   ##   ##   ##  ##    ##      ##      ##   ##  # ## #    ##   #
 ##  ##   ##   ##    ##     ##   ##   ##  ##    ##      ##      ##   ##    ##      ## #
 ##  ##   ##   ##    ##     ##   ##   #####     ##      ##      ##   ##    ##      ####
 ######   ##   ##    ##     ##   ##   ##        ##      ##   #  ##   ##    ##      ## #
 ##  ##   ##   ##    ##     ##   ##   ##        ##      ##  ##  ##   ##    ##      ##   #
 ##  ##    #####    ####     #####   ####      ####    #######   #####    ####    #######
EOF

echo -e "\n[STEP 1] Create a ChatBot at https://t.me/BotFather and copy the access token."
read -p "TELEGRAM_API_TOKEN: " TELEGRAM_API_TOKEN

echo -e "\n[STEP 2] Get the Bitcoin Core credentials from ~/.bitcoin/bitcoin.conf \nto configure the next step."
read -p "BTC_HOST: " BTC_HOST
read -p "BTC_USER: " BTC_USER
read -p "BTC_PASS: " BTC_PASS 
read -p "BTC_ZMQ_TX: " BTC_ZMQ_TX

echo -e "\n[STEP 3] Get the URL of the lnbits service that you will default to."
read -p "LNBITS_DEFAULT_URL: " LNBITS_DEFAULT_URL

echo -e "\n[STEP 4] Get the domain you will use for ChatBot."
read -p "PUBLIC_URL_ENDPOINT: " PUBLIC_URL_ENDPOINT

echo -e "\n[STEP 5] Create an account at https://ngrok.com/ and get the access token."
read -p "NGROK_TOKEN: " NGROK_TOKEN

if [ !LNBITS_DEFAULT_URL ]; then
    LNBITS_DEFAULT_URL="https://legend.lnbits.com"
fi

LNBITS_DEFAULT_URL+="/api"

environment="TELEGRAM_API_TOKEN=${TELEGRAM_API_TOKEN}\n"
environment+="BTC_HOST=${BTC_HOST}\n"
environment+="BTC_USER=${BTC_USER}\n"
environment+="BTC_PASS=${BTC_PASS}\n"
environment+="BTC_PASS=${BTC_ZMQ_TX}\n"
environment+="LNBITS_DEFAULT_URL=${LNBITS_DEFAULT_URL}"

if [[ ! -z "$PUBLIC_URL_ENDPOINT" ]] ; then
    environment+="\nPUBLIC_URL_ENDPOINT=${PUBLIC_URL_ENDPOINT}\n"
    environment+="NGROK_ACTIVE=false"
fi

echo -e $environment > .env

if [[ ! -z "$NGROK_TOKEN" ]]; then 
    ngrok="version: 2\n"
    ngrok+="authtoken: \"${NGROK_TOKEN}\""
    echo -e $ngrok > ./data/ngrok/ngrok.yaml
fi