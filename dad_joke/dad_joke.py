from plugins.base_plugin.base_plugin import BasePlugin
import requests
import textwrap


def split_joke_lines(joke, width=28, max_lines=5):
    if not joke:
        return ["No joke found."]

    wrapped = textwrap.wrap(joke, width=width)
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip(" .,;:-") + "…"
    return wrapped


class DadJoke(BasePlugin):
    def generate_image(self, settings, device_config):
        title = (settings.get("title") or "").strip() or "Dad Joke"
        footer = (settings.get("footer") or "").strip() or "Powered by API Ninjas"

        api_key = device_config.load_env_key("API_NINJAS_KEY")
        if not api_key:
            raise RuntimeError("API Ninjas API key not configured.")

        url = "https://api.api-ninjas.com/v1/dadjokes"
        headers = {"X-Api-Key": api_key}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            content = e.response.text if e.response is not None else "No response content"
            status_code = e.response.status_code if e.response is not None else "unknown"
            raise RuntimeError(f"HTTP error {status_code}: {content}") from e
        except requests.exceptions.Timeout as e:
            raise RuntimeError("Request timed out trying to fetch dad joke data.") from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network or connection error: {str(e)}") from e

        try:
            data = response.json()
        except ValueError as e:
            raise RuntimeError("Failed to parse response as JSON.") from e

        if not isinstance(data, list) or not data:
            raise RuntimeError("Unexpected dad joke data format or no joke returned.")

        joke = data[0].get("joke", "").strip() or "No joke found."
        joke_lines = split_joke_lines(joke)

        width, height = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            width, height = height, width

        return self.render_image(
            dimensions=(width, height),
            html_file="dad_joke.html",
            css_file="dad_joke.css",
            template_params={
                "title": title,
                "joke": joke,
                "joke_lines": joke_lines,
                "footer": footer,
                "plugin_settings": settings
            }
        )

    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params["style_settings"] = True
        template_params["title"] = {
            "required": False,
            "description": "Custom header text",
            "example": "Dad Joke",
        }
        template_params["footer"] = {
            "required": False,
            "description": "Custom footer text",
            "example": "Powered by API Ninjas",
        }
        return template_params