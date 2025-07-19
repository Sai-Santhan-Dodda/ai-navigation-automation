import os
import sys
import asyncio
import argparse
import logging
from typing import Any

from dotenv import load_dotenv
from lmnr import Laminar, Instruments

from browser_use import Agent
from browser_use.llm import ChatOpenAI, ChatOllama, ChatGoogle, ChatGroq
from browser_use.browser.profile import BrowserProfile
from browser_use.browser.session import BrowserSession
from browser_use.browser.types import async_patchright

# Constants for default model names and environment variable keys
DEFAULT_OPENAI_MODEL = "gpt-4.1"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_GOOGLE_MODEL = "gemini-2.0-flash"
DEFAULT_GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

NAVIGATOR_TASK_TEMPLATE = """
0. Do not attempt to login or sign up; assume guest or anonymous access; do not navigate to unrelated sections
or external pages.
1. Remain on the product search results and cart pages. You only need 1 product to checkout.
2. If a popup appears asking to install or run Google Widevine (e.g. "www.bunnings.com.au is asking you to install
and run Google Widevine"), click "Block" or "X" to dismiss it. Do not allow or interact with the installation.
Continue with the page interaction.
3. Go to https://www.bunnings.com.au and wait for full page load.
4. If a location permission modal appears, click "Don't Allow". Continue with the page interaction.
5. In the search bar at the top, enter "{product_name}" and submit.
   If no products appear, stop and report "No products found".
6. From the results, find the product tile matching "{product_name}".
   Click its cart icon in the bottom right.
   If no matching product, report "No matched products found".
7. Wait for the bottom drawer to open; click "Review Cart".
   If it indicates "out of stock", report "Product is out of stock".
8. In "Review Cart" section, if a single "Delivery address" autocomplete field appears:
   8a. Click the "Delivery address" field.
   8b. Type the user's full address (e.g. "{street_address}, {suburb_address} {state} {postcode}") and select the matching suggestion.
   8c. If no suggestion appears, click "Enter address manually" (or similar option) to reveal separate fields, then:
       - Enter street address: "{street_address}".
       - Enter unit (if provided): "{unit}".
       - Enter suburb: "{suburb_address}".
       - Select state: "{state}".
       - Enter postcode: "{postcode}".
   8d. Click "Confirm Address". If unable to proceed, report "Unable to enter delivery address".
9. In "Review Cart", if no collection store is selected, click "Find a store".
10. In the right drawer, enter the user's postcode or suburb: "{location}" in the "Search postcode or suburb" field if they have provided it.
Click on the first search result that says "Available to order" or "Item in Stock". If there are no results, report
"No stores found with this product in stock in your area. You may need to check your postcode or suburb,
try a different product, or try a different store.".
If all the stores say "Unavailable", report "Product found out of stock at all stores".
11. Click on the first store card that says "Available to order" or "Item in Stock". If there are no stores with the
product in stock visible from the current list, check "Show stores with in stock items only" and then click the first
store card with stock. If still no store is found, report "Product found out of stock at all stores".
12. Click on "Click & Collect from <Store Name>" button at the bottom. If unable to proceed, report "Unable to checkout".
13. Click "Continue to checkout". If unable to proceed, report "Unable to checkout".
14. Don't try to fill the contact form or any other form.
15. If you still see "Continue to checkout" if you still see it.
16. That's it! Return the final successful output as "SUCCESS" for evaluation.

"""

def get_llm(provider: str) -> Any:
    """
    Return an LLM instance based on the provider key and environment variables.
    Uses a low temperature (0.1) for deterministic, repeatable outputs.
    """
    temperature = 0.1
    provider = provider.lower()
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise EnvironmentError("OpenAI API key not set in .env")
        return ChatOpenAI(
            model=DEFAULT_OPENAI_MODEL,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=temperature
        )
    if provider == "ollama":
        return ChatOllama(
            model=DEFAULT_OLLAMA_MODEL,
            temperature=temperature
        )
    if provider == "google":
        google_key = os.getenv("GOOGLE_API_KEY")
        if not google_key:
            raise EnvironmentError("Google API key not set in .env")
        return ChatGoogle(
            model=DEFAULT_GOOGLE_MODEL,
            api_key=google_key,
            temperature=temperature
        )
    if provider == "groq":
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise EnvironmentError("Groq API key not set in .env")
        return ChatGroq(
            model=DEFAULT_GROQ_MODEL,
            api_key=groq_key,
            temperature=temperature
        )
    raise ValueError(f"Unsupported provider: {provider}")

def create_browser_session() -> BrowserSession:
    """Create and return a configured BrowserSession instance."""

    # Use Brave browser for anti-bot detection and stealth mode to get around captcha.
    # Detect OS and set Brave browser path accordingly.
    if sys.platform.startswith("darwin"):
        # MacOS default install location for Brave
        brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    elif sys.platform.startswith("win"):
        # Windows default install location for Brave
        brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    elif sys.platform.startswith("linux"):
        # Linux: assume 'brave-browser' is in PATH
        brave_path = "brave-browser"
    else:
        raise RuntimeError("Unsupported OS for browser automation")

    browser_profile = BrowserProfile(
        headless=False,                # Run with UI for easier debugging/interaction
        stealth=True,                  # Enable stealth to avoid bot detection
        keep_alive=True,               # Keep browser alive between actions
        allowed_domains=["*.bunnings.com.au"],  # Restrict navigation to Bunnings domain
        executable_path=brave_path,    # Use OS-detected Brave browser path
        disable_security=False,        # Keep browser security features enabled
        user_data_dir=None,            # Use temporary user data directory
        deterministic_rendering=False, # Allow normal (non-deterministic) rendering
    )
    session = BrowserSession(
        playwright=None,               # Will be set later in async context
        browser_profile=browser_profile,
        browser_path=brave_path        # Use OS-detected Brave browser path
    )
    return session

async def run_bunnings_navigator(
    product_name: str,
    provider: str,
    street_address: str,
    unit: str | None,
    suburb_address: str,
    state: str,
    postcode: str,
) -> None:
    """Autonomously search & checkout a product on Bunnings using the specified LLM."""
    logger.info(f"Starting Bunnings navigator for product '{product_name}' using provider '{provider}'")

    Laminar.initialize(
        project_api_key=os.getenv("LMNR_PROJECT_API_KEY"),
        base_url="http://localhost",
        http_port=8000,
        grpc_port=8001,
        disable_batch=True,
        disabled_instruments={Instruments.BROWSER_USE}
    )
    # PatchRight provides stealth browser automation to help evade bot detection.
    patchright = await async_patchright().start()

    browser_session = create_browser_session()
    browser_session.playwright = patchright

    # Initialize the LLM client
    llm = get_llm(provider)
    # Determine whether to use postcode or suburb for store search
    location_value = postcode if postcode else suburb_address
    task = NAVIGATOR_TASK_TEMPLATE.format(
        product_name=product_name,
        location=location_value,
        street_address=street_address,
        unit=unit or "",
        suburb_address=suburb_address,
        state=state,
        postcode=postcode,
    )
    agent = Agent(
        task=task,
        llm=llm,
        browser_session=browser_session,
        max_actions_per_step=5,
    )
    result = await agent.run(max_steps=50)
    return result.final_result()

def main() -> None:
    """Parse CLI args and execute the Bunnings navigator."""
    parser = argparse.ArgumentParser(
        description="Autonomously search & checkout a product on Bunnings.com.au"
    )
    parser.add_argument(
        "-q", "--query",
        help="The exact product name to search for (in quotes if it contains spaces)",
    )
    parser.add_argument(
        "-p", "--provider",
        choices=["openai", "ollama", "google", "groq"],
        default="openai",
        help="LLM provider to use"
    )
    parser.add_argument("--street-address",
                        help="Street number and name for delivery address")
    parser.add_argument("--unit",
                        help="Unit, building, level, etc. for delivery address")
    parser.add_argument("--suburb-address",
                        help="Suburb for delivery address")
    parser.add_argument("--state",
                        help="State abbreviation (e.g. VIC, NSW) for delivery address")
    parser.add_argument("--postcode",
                        help="Postcode for delivery address")
    args = parser.parse_args()

    try:
        result_text = asyncio.run(run_bunnings_navigator(
            args.query,
            args.provider,
            args.street_address,
            args.unit,
            args.suburb_address,
            args.state,
            args.postcode,
        ))
        # Print the final successful output for evaluation
        return result_text
    except KeyboardInterrupt:
        logger.error(f"Operation cancelled by user. Args: {args}")
        sys.exit(1)
    except Exception:
        logger.exception(f"Error running navigator. Args: {args}")
        sys.exit(1)

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
