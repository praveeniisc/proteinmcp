import os
import json
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple

CONFIG_DIR = Path.home() / ".proteinmcp"
CONFIG_FILE = CONFIG_DIR / "config.json"

def get_config_path() -> Path:
    """Returns the path to the configuration file, creating the directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_FILE

def load_config() -> dict:
    """Loads configuration from config.json. Returns default config if file doesn't exist."""
    path = get_config_path()
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading configuration file: {e}")
    
    return {
        "provider": "google",
        "gemini_api_key": "",
        "gemini_model": "gemini-1.5-flash",
        "openai_api_key": "",
        "openai_model": "gpt-4o-mini"
    }

def save_config(config: dict) -> None:
    """Saves the configuration to config.json."""
    path = get_config_path()
    try:
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")

def validate_gemini_key(api_key: str) -> Tuple[bool, str]:
    """Validates the Gemini API key using a simple REST request."""
    if not api_key:
        return False, "API key is empty."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{
                "text": "Say 'ok'."
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return True, "Key is valid."
        else:
            try:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
            except Exception:
                error_msg = response.text
            return False, f"API returned error status {response.status_code}: {error_msg}"
    except Exception as e:
        return False, f"Connection failed: {e}"

def validate_openai_key(api_key: str) -> Tuple[bool, str]:
    """Validates the OpenAI API key using a simple REST request."""
    if not api_key:
        return False, "API key is empty."
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say 'ok'."}],
        "max_tokens": 5
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return True, "Key is valid."
        else:
            try:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
            except Exception:
                error_msg = response.text
            return False, f"API returned error status {response.status_code}: {error_msg}"
    except Exception as e:
        return False, f"Connection failed: {e}"


def interactive_configure() -> None:
    """Interactively configures providers and API keys using Click prompts."""
    import click

    click.echo("\n⚙️  ProteinMCP Interactive Configuration")
    click.echo("========================================")

    config = load_config()

    # Provider Selection
    provider = click.prompt(
        "Select default LLM provider",
        type=click.Choice(["google", "openai"]),
        default=config.get("provider", "google")
    )
    config["provider"] = provider

    if provider == "google":
        # Gemini setup
        click.echo("\n--- Google Gemini Setup ---")
        current_key = config.get("gemini_api_key", "")
        key_masked = f"...{current_key[-6:]}" if len(current_key) > 6 else ""
        prompt_msg = f"Enter Gemini API key"
        if key_masked:
            prompt_msg += f" (current: {key_masked})"
        
        api_key = click.prompt(prompt_msg, hide_input=True, default=current_key, show_default=False)
        
        if api_key and api_key != current_key:
            click.echo("🔄 Validating API key...")
            valid, msg = validate_gemini_key(api_key)
            if valid:
                click.echo("✅ API key is valid!")
                config["gemini_api_key"] = api_key
            else:
                click.echo(f"❌ Validation failed: {msg}")
                if click.confirm("Save this key anyway?", default=False):
                    config["gemini_api_key"] = api_key
        elif api_key:
            config["gemini_api_key"] = api_key
            
        model = click.prompt(
            "Default Gemini model",
            default=config.get("gemini_model", "gemini-1.5-flash")
        )
        config["gemini_model"] = model

    elif provider == "openai":
        # OpenAI setup
        click.echo("\n--- OpenAI Setup ---")
        current_key = config.get("openai_api_key", "")
        key_masked = f"...{current_key[-6:]}" if len(current_key) > 6 else ""
        prompt_msg = f"Enter OpenAI API key"
        if key_masked:
            prompt_msg += f" (current: {key_masked})"
            
        api_key = click.prompt(prompt_msg, hide_input=True, default=current_key, show_default=False)
        
        if api_key and api_key != current_key:
            click.echo("🔄 Validating API key...")
            valid, msg = validate_openai_key(api_key)
            if valid:
                click.echo("✅ API key is valid!")
                config["openai_api_key"] = api_key
            else:
                click.echo(f"❌ Validation failed: {msg}")
                if click.confirm("Save this key anyway?", default=False):
                    config["openai_api_key"] = api_key
        elif api_key:
            config["openai_api_key"] = api_key
            
        model = click.prompt(
            "Default OpenAI model",
            default=config.get("openai_model", "gpt-4o-mini")
        )
        config["openai_model"] = model

    save_config(config)
    click.echo("\n✨ Configuration saved successfully!")

