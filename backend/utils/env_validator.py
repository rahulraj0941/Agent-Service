import os
import sys


def validate_environment():
    """Validate required environment variables for Gemini API are set."""
    required_vars = {
        "GOOGLE_API_KEY": "Google API key for Gemini",
        "LLM_PROVIDER": "LLM provider (should be 'google')",
        "LLM_MODEL": "LLM model name (should be 'gemini-2.5-flash' or similar)"
    }
    
    missing_vars = []
    warnings = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"  - {var}: {description}")
        elif var == "LLM_MODEL" and "1.5" in value:
            warnings.append(
                f"  - {var} is set to '{value}' which may be deprecated. "
                f"Consider using 'gemini-2.5-flash' or newer."
            )
    
    if missing_vars:
        print("ERROR: Missing required environment variables:", file=sys.stderr)
        print("\n".join(missing_vars), file=sys.stderr)
        print("\nPlease set these in your .env file or environment.", file=sys.stderr)
        return False
    
    if warnings:
        print("WARNING: Environment configuration issues:", file=sys.stderr)
        print("\n".join(warnings), file=sys.stderr)
    
    print("Environment validation: OK")
    return True


if __name__ == "__main__":
    if not validate_environment():
        sys.exit(1)
