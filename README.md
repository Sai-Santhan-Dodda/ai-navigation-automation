# Browser Use Automation Agent

This project implements a browser automation agent for `Bunnings website` using the `browser-use` library, orchestrated via the `laminar` framework, managed with `uv` for Python environments, and running in Brave Browser for stealth and CAPTCHA bypass.

[AI Website Automation Project Demo Video](https://www.loom.com/share/9469c70441aa49778e2aae779c4367bc?sid=4a853ef7-ca68-4ed7-90ec-c138cb912a12)

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [AI Documentation](#ai-documentation)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Evaluation](#evaluation)
- [Contributing](#contributing)
- [License](#license)

## Overview

The agent leverages browser automation to perform tasks programmatically, using Python 3.13, Browser Use for browser control, laminar for orchestration and evaluation, uv for environment management, and Brave Browser for stealth and CAPTCHA bypass.

## How It Works

This automation agent combines several technologies to understand and interact with web pages based on user goals.

**Browser Use** is a Python library designed for browser automation, its a Playwright wrapper leveraging the capabilities of large language models (LLMs) for tasks such as web navigation, data extraction, and form filling. It provides a flexible and scalable framework for automating browser interactions, making it suitable for a wide range of applications, from simple scripts to complex automation tasks.

- **LLM Integration**: Utilizes LLMs for decision-making and task execution, allowing for more intelligent and adaptive automation.

- **Browser Automation**: Supports automation of browser interactions, including navigation, clicking, typing, and data extraction.

- **Extensive Model Support**: Officially supports multiple LLMs, including OpenAI, Anthropic, Google, Groq, Ollama, and DeepSeek, with the capability to integrate other models through compatible APIs.

- **Modular Design**: Features a modular structure that allows for easy extension and customization of its functionalities.

**AI (Large Language Models)**: The agent's brain is powered by an AI model (like OpenAI's GPT, Google's Gemini, or a local Ollama model). The model receives the user's high-level objective (e.g., "find a chair") and a simplified version of the current web page's HTML. It then decides the best next action to take to move closer to the goal.

**Brave Browser**: Used along with patchright for stealth browsing, CAPTCHA solving, and Cloudflare bypass.

**Laminar**: Laminar is used as the evaluation and orchestration controller for the browser automation tasks. Tasks are run under Laminar’s supervision, providing structured logging, evaluation metrics, and easy integration into CI pipelines.

## AI Documentation

### AI Decision Making and Edge Cases

The agent operates in a loop to achieve the user's objective:

1. **Goal & Context**
   Start with the user’s high-level goal and the current URL.
2. **Analyze the Page**
   Capture the page state (e.g., via screenshot and element detection) to map clickable buttons, inputs, links, etc.
3. **Consult the AI**
   Send the goal, URL, and page map to the LLM.
4. **Receive Action**
   The AI model returns a specific command in a structured format (JSON), such as `{"action": "click", "element_id": "login-button"}` or `{"action": "type", "element_id": "search-bar", "text": "chair"}`.
5. **Execute Action**
   Automation (Playwright) performs the command.

This cycle repeats—analyzing, deciding, executing—until the task completes or a predefined step limit is reached.

**Edge Case Handling**:

- **Dynamic Content**: By re-analyzing the page's HTML and also looking at the screenshot at every step, the agent can adapt to web pages that change dynamically after an action is performed.
- **Errors**: If an action fails (e.g., an element to click is not found), the agent reports the failure. The current implementation stops on failure, but it could be extended to ask the AI for an alternative action.
- **Complex Tasks**: The AI's reasoning capabilities allow it to break down a complex, multi-step task (like filling a multi-page form) into a sequence of smaller, manageable actions.

### Algorithms and Models

The core "algorithm" is a state-driven planning process orchestrated by a Large Language Model (LLM). There isn't a traditional, hard-coded algorithm for web interaction. Instead, the agent relies on the general reasoning and pattern-matching abilities of the pre-trained LLM.

The model's task is to map the high-level goal and the current page state to the most logical, low-level browser action. The effectiveness of the agent is therefore highly dependent on the capabilities of the chosen language model (e.g., GPT-4, Llama 3, etc.).

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - python environment manager

## Installation

### Setting up the virtual environment

```bash
uv venv --python 3.13
source .venv/bin/activate
```

### Installing dependencies

```bash
uv sync --all-extras
```

### Installing Brave browser (To get around bot detection and captcha)

Refer Brave browser installation instructions from https://brave.com/brave-browser/

## Configuration

Copy the `.env.example` file as `.env` file in the project root directory. Add your LLM Provider API keys to the `.env` file or run an LLM locally using [Ollama](https://ollama.com/). You can change all the model names by changing the `DEFAULT_OLLAMA_MODEL`, `DEFAULT_OPENAI_MODEL`, `DEFAULT_GOOGLE_MODEL`, and `DEFAULT_GROQ_MODEL` variables in the `automation_agent.py` file.

## Usage

### Running the agent with OpenAI after adding OpenAI API key to the `.env` file

```bash
uv run automation_agent.py -q "chair" -p openai
```

### Running the agent with Ollama

```bash
uv run automation_agent.py -q "4 step ladder" -p ollama --postcode "3000"
```

### Running the agent with Google after adding Google API key to the `.env` file

```bash
uv run automation_agent.py -q "2 step ladder" -p google --suburb-address "Anytown"
```

### Running the agent with Groq after adding Groq API key to the `.env` file

```bash
uv run automation_agent.py -q "treadmill" -p groq --street-address "123 Main St" --unit "Apt 4B" --suburb-address "Anytown" --state "VIC" --postcode "3000"
```

## Evaluation Setup

### If you don't have the standalone `lmnr` directory, clone Laminar repository into a separate directory from `browser-use-implementation` directory. Refer to the [Laminar self-hosting setup](https://docs.lmnr.ai/self-hosting/setup) for more information on how to self-host Laminar.

### Navigate to the `lmnr` directory and run the following command to start the Laminar server (`docker` is required)

```bash
cd lmnr
docker compose up -d
```

### If everthing is setup correctly, you should be able to access the Laminar dashboard running at http://localhost:5667 in your preferred browser

### Create a project in the Laminar dashboard and generate an API key for that project and add it to the `.env` file

### Running the agent success rate evaluation with Laminar

```bash
uv run agent_evaluation.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
Make sure to run tests and update them as appropriate.

## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
