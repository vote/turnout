# Turnout ECS Tasks

These are the ECS task definitions for deploying Turnout.

We use [Jsonnet](https://jsonnet.org/) for templating. DO NOT edit the JSON files in `generated/`; edit the template in `template/` instead.

## Building

Before committing, you need to build the JSON files from the Jsonnet templates so that Spinnaker can pull the compiled JSON directly from this repo.

Run `./build.sh`. This will run `jsonnetfmt` over the jsonnet templates (to format/lint them), and then use them to generate the JSON files.
