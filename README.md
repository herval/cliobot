# Cliobot - multimodal generative AI bot for chat platforms

Cliobot is a modular bot platform for generative AI agents. It's goal is to provide a simple, easy to use and extendable platform for running generative AI agents that can handle audio, video, text and images, on any chat platform. 

It can be easily extend it to use multiple APIs and services, from Stable Diffusion to OpenAI, and you can run it on your own device or deploy it online. 

It comes with multiuser handling out of the box, and minimal dependencies (everything stays in memory by default).

Currently it supports Telegram out of the box, with other platforms coming soon


## Key Features

- Full i18n support, with english and brazilian portuguese out of the box
- Multiuser support


## Installing

Running a bot locally is simple:

- Clone this repo
- Setup the python env
- Rename .env.example to .env.development and set the appropriate variables you want. 


### Running Cliobot on Telegram

The bare minimum you'll need is an API Token for a Telegram bot. Please refer to the [official documentation](https://core.telegram.org/bots/tutorial#obtain-your-bot-token) for how to obtain an API token. It should look like this: `4839574812:AAFD39kkdpWt3ywyRZergyOLMaJhac60qc`

Once you get a token, change your `.env.development` to include the following two lines:

```
BOT_PLATFORM=telegram
TELEGRAM_APP_TOKEN=your_token_here
```


## Built-in extensions

These are all deactivated by default, but easily enabled:

- Sentry.io support for error reporting/tracking
- Automatic message translation using Google Translate API
- Utilization metrics using MixPanel



## Configuring



## Running on K8s



## Writing plugins



## Planned features

- Discord integration
- Whatsapp integration