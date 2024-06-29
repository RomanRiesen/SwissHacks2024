### A(p)I Testing

This is the result of a 36h hackathon ([SwissHack](https://www.swisshacks.com/)® organized by Tenity®) where we cooperated with PostFinance® to explore opportunities to support the business and implementation side in API testing using large language models.

### Requirements

A [dev-container](https://code.visualstudio.com/docs/devcontainers/containers) enabled IDE should just be able to open the project and get you up and running.

### Downloading

If you want to use keys:

`git clone --recurse-submodules git@github.com:RomanRiesen/SwissHacks2024.git`

if you want to use a token:

`git clone --recurse-submodules https://github.com/RomanRiesen/SwissHacks2024.git`

or if you cloned it already

`git submodule update --init` in both `./postfinance` then in `./postfinance/source`

To run this you'll further need an OpenAI API key in the env variable `OPENAI_KEY`.
