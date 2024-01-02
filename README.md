# Cliobot - multimodal generative AI bot for chat platforms

![Clio Bot](clio.jpg)

Cliobot is a modular bot platform for generative AI agents. It's goal is to provide a simple, easy to use and extendable platform for running generative AI agents that can handle audio, video, text and images, on any chat platform. 

It can be easily extend it to use multiple APIs and services, from Stable Diffusion to OpenAI, and you can run it on your own device or deploy it online. 

It comes with Telegram support and multiuser handling out of the box, and minimal dependencies (everything stays in memory by default).


## The Basic

Cliobot has two main working modes: __command mode__ or __LLM mode__

In __command mode__, you interact by using __slash commands__ (messages starting with a /). It comes with a set default of slash commands and you can easily create yor own.

[WIP] In __LLM mode__, the bot works like chatgpt & other multimodal chatbots out there: it follows a configurable system prompt that defines its core behavior and can use functions to perform actions (including executing code or browsing the web).

Notice both modes use the same command definitions, so the only difference between them is a tradeoff between more natural language interpretation versus cost (since running GPT4 & other models can get expensive quickly).


## Command syntax

Cliobot uses a simple prompt parsing system (common across apps such as Midjourney & others). It's based on the following format:

```
/<command> <text prompt>? [--<param_name> <value>]+
```

Each command handler is defined as a pydantic model, and the parameters are automatically parsed and validated.

When a certain command requires multiple inputs, such as image, the bot will ask for them in sequence, then run the command after you provide all the inputs.

An example of a command using the default replicate-backed image generation command would be as follows:

```
.......
```


## Key features

- OpenAI API support for DALL-E, GPT-3, GPT-4 and Whisper, including Azure support and multiple API keys
- Multiuser support
- File storage support (local & S3)
- Automatic message translation using Google Translate API


## Installing

Running a bot locally is simple:

- Clone this repo
- Setup the python env
- Rename `config.yml.example` to `config.yml` and set the appropriate variables you want. 


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

TODO


## Writing plugins



## Planned features

- S3 file storage
- 
- Discord integration
- Whatsapp integration

