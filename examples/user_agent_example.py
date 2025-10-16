#!/usr/bin/env python3

"""Example demonstrating custom User-Agent usage with ApiClient."""

from bw_serve_client import ApiClient


def main():
  """Demonstrate different User-Agent configurations."""
  # Default User-Agent
  print("=== Default User-Agent ===")
  client1 = ApiClient()
  print(f"User-Agent: {client1.session.headers['User-Agent']}")

  # Custom User-Agent
  print("\n=== Custom User-Agent ===")
  client2 = ApiClient(user_agent="MyBitwardenApp/2.1.0")
  print(f"User-Agent: {client2.session.headers['User-Agent']}")

  # Another custom User-Agent
  print("\n=== Another Custom User-Agent ===")
  client3 = ApiClient(user_agent="BitwardenCLI-Integration/1.0.0")
  print(f"User-Agent: {client3.session.headers['User-Agent']}")

  # Using with context manager
  print("\n=== Using with Context Manager ===")
  with ApiClient(user_agent="ContextManagerApp/1.0.0") as client4:
    print(f"User-Agent: {client4.session.headers['User-Agent']}")
    # In a real scenario, you would make API calls here
    # data = client4.get("/api/items")

  print("\nAll examples completed successfully!")


if __name__ == "__main__":
  main()
