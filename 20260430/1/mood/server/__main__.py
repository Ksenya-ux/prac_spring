import asyncio
from .server import run_server


def main():
    print("Starting MOOD server...")
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
    
