### A(p)I Testing

This is the result of a 36h hackathon ([SwissHack](https://www.swisshacks.com/)® organized by Tenity®) where we cooperated with PostFinance® to explore opportunities to support the business and implementation side in API testing using large language models.

The goal was to find bugs in a provided API by using LLMs to generate tests from user studies and an openAPI spec.

We provide a cli application that can has two working modes; interactive and exhaustive. In the interactive mode the user can put in new user stories for which then a plan (a list of tests) is created. This list is then successively worked through, allowing the user to regenerate tests for plans until they are satisfying (or skipping testing ideas entirely).

Having a second pair of ~~eyes~~ tokenizers to work out edge cases in writing tests has proven helpful even during the hackathon.

### Downloading

Don't forget to load the submodules recursively.

If you want to use keys:

`git clone --recurse-submodules git@github.com:RomanRiesen/SwissHacks2024.git`

if you want to use a token:

`git clone --recurse-submodules https://github.com/RomanRiesen/SwissHacks2024.git`

or if you cloned it already

`git submodule update --init` in both `./postfinance` then in `./postfinance/source`

To run this you'll further need an OpenAI API key in the env variable `OPENAI_KEY`.

### Running

#### Requirements

A [dev-container](https://code.visualstudio.com/docs/devcontainers/containers) enabled IDE should just be able to open the project and get you up and running.

#### Target Application

The target application we tested is under `postfinance/source` as are instructions on how to run it.
