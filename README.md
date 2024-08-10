# llm-rename

Small [`llm`](https://llm.datasette.io/) plugin designed to assist with `qcp/qmv` execution plans.

Once you install the plugin, you can run `qmv --editor 'llm rename'` and it will -

- Append a default prompt to the plan
- Open `$EDITOR` to let you change the plan/prompt
- Use `llm` to ask an LLM to mutate the plan using the prompt
- Deliver the mutated plan back to `qcp/qmv`

# Installation

`llm install llm-rename`
