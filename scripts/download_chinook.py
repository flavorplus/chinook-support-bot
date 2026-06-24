import pathlib
import requests

CHINOOK_URL = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "Chinook.db"


def download_database(destination: pathlib.Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Chinook database to {destination}")
    response = requests.get(CHINOOK_URL, stream=True, timeout=30)
    response.raise_for_status()
    with destination.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                handle.write(chunk)
    print("Download complete.")


if __name__ == "__main__":
    download_database(DB_PATH)
