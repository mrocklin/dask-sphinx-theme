import dask_sphinx_theme
import requests
import yaml
from docutils import nodes
from docutils.parsers.rst import Directive, directives


def get_remote_yaml(url):
    r = requests.get(url, headers={'User-Agent': f'Dask sphinx theme {dask_sphinx_theme.__version__}'})
    try:
        return yaml.safe_load(r.text)
    except Exception as e:
        print(f"Failed to load {url} with text {r.text}")
        raise e


class DaskConfigDirective(Directive):
    option_spec = {
        "location": directives.unchanged,
        "schema": directives.uri,
        "config": directives.uri,
    }

    def run(self):
        location = self.options["location"]
        config = self.options["config"]
        print(f"\n\n\n[file] {config = }\n\n\n")
        schema = self.options["schema"]
        print(f"\n\n\n[file] {schema = }\n\n\n")

        print("Attempting to run get_remote_yaml(config)...")
        config = get_remote_yaml(config)
        print(f"\n\n\n{config = }\n\n\n")
        schema = get_remote_yaml(schema)
        print(f"\n\n\n{schema = }\n\n\n")

        for k in location.split("."):
            # dask config does not have a top level key
            # we need to pass full schema and config
            if k == "dask":
                schema = schema
                config = config
            else:
                config = config[k]
                schema = schema["properties"].get(k, {})
        html = generate_html(config, schema, location)
        return [nodes.raw("", html, format="html")]


def setup(app):
    app.add_directive("dask-config-block", DaskConfigDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def dask_config_to_html(key, value, schema, prefix=""):
    if isinstance(value, dict):
        return sum(
            (
                dask_config_to_html(
                    k,
                    v,
                    schema.get("properties", {}).get(k, {"properties": {}}),
                    prefix=prefix + key + ".",
                )
                for k, v in value.items()
            ),
            [],
        )

    else:
        try:
            description = schema["description"]
            description = description.strip()
        except KeyError:
            description = "No Comment"

        if "dask." in prefix:
            prefix = prefix.replace("dask.", "")

        key = prefix + key
        value = str(value)
        node = f"""<dl class="py data">
                     <dt id="{key}">
                       <code class="sig-prename descclassname">{key}</code>
                       <em class="property">&nbsp;&nbsp;{value}</p></em>
                       <a class="headerlink" href="#{key}" title="Permalink to this definition">¶</a>
                     </dt>
                    <dd><p>{description}</p></dd>
                    </dl>

                """
        return [node]


def generate_html(config, schema, location):
    nested_html = dask_config_to_html(
        key="", value=config, schema=schema, prefix=location
    )
    return "".join(nested_html)
