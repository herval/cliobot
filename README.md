# Cliobot - multimodal generative AI bot for chat platforms

![Clio Bot](clio.jpg)

Cliobot is a modular bot platform for generative AI agents. It's goal is to provide a simple, easy to use and extendable
platform for running generative AI agents that can handle audio, video, text and images, on any chat platform.

It can be easily extend it to use multiple APIs and services, from Stable Diffusion to OpenAI, and you can run it on
your own device or deploy it online.

It comes with Telegram support and multiuser handling out of the box, and minimal dependencies.

Important: This repo is a work in progress - I'm porting over code from a startup I was working on, so it's still a bit
rough and subject to multiple rewrites.

## The Basic

Cliobot has two main working modes: __command mode__ or __LLM mode__

In __command mode__, you interact by using __slash commands__ (messages starting with a /). It comes with a set default
of slash commands and you can easily create yor own.

[WIP] In __LLM mode__, the bot works like chatgpt & other multimodal chatbots out there: it follows a configurable
system prompt that defines its core behavior and can use functions to perform actions (including executing code or
browsing the web).

Notice both modes use the same command definitions, so the only difference between them is a tradeoff between more
natural language interpretation versus cost (since running GPT4 & other models can get expensive quickly).

## Built-in commands

Cliobot comes with a set of built-in commands that you can use out of the box. You can also easily add your own
commands!

### /image

Generates an image from a text prompt.

Built-in implementations: DALL-E 3, any image model hosted on Replicate.com.

### /describe [WIP]

Describe an image using text.

Built-in implementations: OpenAI GPT4V, Ollama (Llava, etc), any image to text model hosted on Replicate.com.

### /transcribe

Transcribes an audio file into text.

Built-in implementations: OpenAI Whisper-1

### /ask

Ask a question to an LLM agent. This doesn't take any conversation context.

Built-in implementations: GPT-4 or any model supported by [Ollama](https://github.com/jmorganca/ollama) running in
server mode, any LLM hosted on Replicate.com.

### /chat [WIP]

Chat with an LLM agent, including a backlog of context

## Command syntax

Cliobot uses a simple prompt parsing system (common across apps such as Midjourney & others). It's based on the
following format:

```
/<command> <text prompt>? [--<param_name> <value>]+
```

Each command handler is defined as a pydantic model, and the parameters are automatically parsed and validated.

When a certain command requires multiple inputs, such as image, the bot will ask for them in sequence, then run the
command after you provide all the inputs.

An example of a command using the default dalle3 image generation command would be as follows:

```
/dalle3 a giant hamster in space --size 1024x1024
```

## Installing

Running a bot locally is simple:

- Clone this repo
- Setup the python env
- Rename `config.example.yml` to `config.yml` and set the appropriate variables you want.
- Install all dependencies with:

```
python -m venv create venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Cliobot on Telegram

The bare minimum you'll need is an API Token for a Telegram bot. Please refer to
the [official documentation](https://core.telegram.org/bots/tutorial#obtain-your-bot-token) for how to obtain an API
token. It should look like this: `4839574812:AAFD39kkdpWt3ywyRZergyOLMaJhac60qc`

Once you get a token, change your `config.yml` to include the following session:

```
bot:
  platform: telegram
  token: "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
```

Then, run the bot using the following command:

```
source venv/bin/activate
python app.py
```

## Running with Docker

If you don't have Python on your system or just prefer to keep things simple, you can run Cliobot using Docker too:

```
docker build -t cliobot .
docker run -it --rm -v $(pwd)/data:/content/data -v $(pwd)/.env:/content/.env -v $(pwd)/config.yml:/content/config.yml cliobot
```

## Using Automatic1111 WebUI as a backend

You can plug in [Automatic1111 WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) and use it as a backend for image generation! To do so, you'll need to set the following variables on your config.yml:

```
webui:
    endpoint: http://localhost:7860
    auth: user:pass
```

Notice you'll need to start webui with the `--api` flag. The `auth` field is optional (you can leave it blank if you don't use API authentication). For more information on how to use the API, please refer to the [official documentation](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API).

### Supported operations

You can use any Stable Diffusion model that's installed along webui with the `/image` command. The following parameters are supported:

```
steps: int = 20
sampler: str = 'DPM++ 2M SDE'
width: int = 512
height: int = 512
batchcount: int = 1
batchsize: int = 1
cfg: int = 7
seed: int = -1
negative: str = ''
```

## Configuring OpenAI

To use OpenAI models (gpt, dalle3, whisper, etc), include the following in your config.yml:

```
openai:
  endpoints:
    - api_key: sk-....
      api_type: open_ai
      base_url: https://api.openai.com/v1/

    - api_key: xxx
      api_type: azure
      api_version: 2023-10-01-preview
      base_url: https://xxx.openai.azure.com
      model: gpt4
      kind: gpt-4

    - api_key: xxx
      api_type: azure
      api_version: 2
      base_url: https://xxx.openai.azure.com
      model: embeddings
      kind: embeddings

    - api_key: xxx
      api_type: azure
      api_version: 2023-12-01-preview
      base_url: https://xxx.openai.azure.com
      model: dalle3
      kind: dall-e-3

    - api_key: xxx
      api_type: azure
      api_version: 2023-12-01-preview
      base_url: https://xxx.openai.azure.com
      model: whisper1
      kind: whisper-1
``` 

Notice that for Azure deployments, you'll need to set one entry per model
kind (`dall-e-3`, `whisper-1`, `embeddings`, `gpt-4`). The API key can be the same for all of them.

## Configuring Ollama

In order to use any LLM via Ollama, simply include the following in your config.yml:

```
ollama:
  endpoint: http://localhost:11434
  models:
    - llama2
```

Each model on the `models` list will be exposed as a model on the bot. You can then use it by using the `/ask` command:

```
/ask what's the meaning of life? --model llama2
```

## Configuring Replicate

You can use any model hosted on [Replicate](https://replicate.com/) by mapping it out on your config.yml. The mapping is
a bit more involved than other models, since you need to map out each parameter. Here's a complete example using SDXL
hosted on Replicate:

```
replicate:
  api_token: xxx
  endpoints:
    - model: 'sdxl'
      kind: 'image'
      version: 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b'
      params:
        prompt:
          kind: str
          required: true
        negative_prompt:
          alias: no
          kind: str
        width:
          kind: int
          default: 1024
        height:
          kind: int
          default: 1024
        num_outputs:
          alias: num
          kind: int
          default: 1
        num_inference_steps:
          alias: steps
          kind: int
          default: 25
        guidance_scale:
            alias: cfg
            kind: float
            default: 7.5
        prompt_strength:
            alias: ps
            kind: float
            default: 0.8
        seed:
            kind: int
        apply_watermark:
            alias: watermark
            kind: bool
            default: true
        scheduler:
            kind: str
            default: 'KarrasDPM'
        refine:
            kind: str
            alias: refiner
            default: 'no_refiner'
            value_map:
              no: no_refiner
              expert: expert_ensemble_refiner
              base: base_image_refiner
        refine_steps:
            kind: int
            alias: rs
```

With the above config, you'll be able to generate images using the following command:

```
/image photo of a giant hamster in space --model sdxl --no illustration, cartoon, drawing --width 1280 --num 4 --steps 50 --rs 8 --refiner expert
```

Notice the parameter names on your slash command will match the param name on the config, _or_ an optional `alias`. This
allows you to use shorter parameter names on your commands (eg typing out `--no` instead of `--negative_prompt`).

## Built-in extensions

These are all deactivated by default, but easily enabled:

- Sentry.io support for error reporting/tracking
- Automatic message translation using Google Translate API
- Utilization metrics using MixPanel
- S3 for file storage

## Features

- OpenAI API support for DALL-E, GPT-3, GPT-4 and Whisper, including Azure support and multiple API keys
- Ollama support for any LLM model (including image to text)
- Support for any model hosted on Replicate.com
- Multiuser support
- File storage support (local & S3)
- Automatic message translation using Google Translate API
- Persistent preferences to reduce repetitive prompt parameters

## Running on K8s

TODO

## Writing plugins

TODO

## Planned features

- Discord integration
- Whatsapp integration
- Stable Diffusion
- StableHorde processing

## TODO

- RAG mode
- chat history
- Finish the LLM mode
- save generated images to storage
- save uploads
- i18n support
- img2txt commands
- llama implementation

