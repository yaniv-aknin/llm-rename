# llm-rename

Small [`llm`](https://llm.datasette.io/) plugin designed to assist with `qcp`/`qmv` execution plans.

Once you install the plugin, you can run `qmv --editor 'llm rename'` and it will -

- Append a default prompt to the plan
- Open `$EDITOR` to let you change the plan/prompt
- Use `llm` to ask an LLM to mutate the plan using the prompt
- Deliver the mutated plan back to `qcp`/`qmv`

Note you can add `-E`/`--edit-after` to review and change the plan after the LLM edited it.

If you editor is `vim`, you can always exit non-zero (using `:cq`), which will allow you to abort
any `qcp`/`qmv` changes.

# Installation

After you installed `llm` itself (e.g., `pipx install llm`), use:

`llm install llm-rename`
