from pathlib import Path
import llm
import click
import os
import subprocess
import typing as t

import pydantic

MARKER = os.environ.get("LLM_RENAME_MARKER", "\n==\n")

DEFAULT_SYSTEM_PROMPT = "You are given a qcp/qmv execution plan. Please emit a revised plan, and nothing else, following the criteria below:\n  * cleanup excessive whitespace\n"


def edit(plan_file: Path):
    editor = os.environ.get("EDITOR", "vim")
    try:
        subprocess.run([editor, str(plan_file)], check=True)
    except subprocess.CalledProcessError:
        raise SystemExit("Error: editor returned non-zero exit code")


def process_plan(
    plan_file: Path, system_prompt: str, call_llm: t.Callable[[str, str], str]
):
    with open(plan_file, "a") as handle:
        handle.write(MARKER)
        handle.write(system_prompt)
    edit(plan_file)
    raw_content = plan_file.read_text()
    if raw_content.count(MARKER) != 1:
        raise SystemExit("Error: expected exactly one marker")
    plan_content, system_prompt = raw_content.split(MARKER)
    revised_plan = call_llm(plan_content, system_prompt)
    plan_file.write_text(revised_plan)


@llm.hookimpl
def register_commands(cli):
    from llm.cli import (
        load_template,
        get_default_model,
        get_model,
        get_key,
        render_errors,
        Template,
    )

    @cli.command()
    @click.argument("plan_file", type=click.Path(exists=True, path_type=Path))
    @click.option("model_id", "-m", "--model", help="Model to use")
    @click.option(
        "options",
        "-o",
        "--option",
        type=(str, str),
        multiple=True,
        help="key/value options for the model",
    )
    @click.option("-s", "--system", help="System prompt to use")
    @click.option("-t", "--template", help="Template to use")
    @click.option(
        "-p",
        "--param",
        multiple=True,
        type=(str, str),
        help="Parameters for template",
    )
    @click.option(
        "-E",
        "--edit-after",
        is_flag=True,
        default=False,
        help="Edit the plan again after LLM processing",
    )
    @click.option("--key", help="API key to use")
    def rename(
        plan_file,
        model_id,
        options,
        system,
        template,
        param,
        edit_after,
        key,
    ):
        "LLM based qcp/qmv execution plan editors"
        if model_id is None:
            model_id = get_default_model()
        try:
            model = get_model(model_id)
        except KeyError:
            raise click.ClickException("'{}' is not a known model".format(model_id))
        if model.needs_key:
            model.key = get_key(key, model.needs_key, model.key_env_var)

        validated_options = {}
        if options:
            try:
                validated_options = dict(
                    (key, value)
                    for key, value in model.Options(**dict(options))
                    if value is not None
                )
            except pydantic.ValidationError as ex:
                raise click.ClickException(render_errors(ex.errors()))
        validated_options["stream"] = False

        template_obj = None
        if template:
            params = dict(param)
            if system:
                raise click.ClickException(
                    "Cannot use -t/--template and --system together"
                )
            template_obj = load_template(template)
            if model_id is None and template_obj.model:
                model_id = template_obj.model

        if template_obj:
            try:
                prompt, system = template_obj.evaluate("", params)
                if prompt:
                    raise click.ClickException(
                        "Must use template without a user prompt"
                    )
            except Template.MissingVariables as ex:
                raise click.ClickException(str(ex))

        if not system:
            system = DEFAULT_SYSTEM_PROMPT

        def call_llm(user_prompt: str, system_prompt: str) -> str:
            return model.prompt(user_prompt, system_prompt, **validated_options).text()

        process_plan(plan_file, system, call_llm)

        if edit_after:
            edit(plan_file)
