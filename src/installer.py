import os
import tempfile
import zipfile
import requests
import shutil
import json
from pathlib import Path
from tqdm import tqdm
from rich.console import Console
from rich.progress import track

# Setup rich console
console = Console()

def download_file(url, dest_path):
    try:
        console.print(f"[blue]Downloading file from {url}...[/blue]")
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        total_size = int(response.headers.get('content-length', 0))
        with open(dest_path, "wb") as file, tqdm(
            desc="Downloading",
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            colour="green"
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                bar.update(len(chunk))
        console.print(f"[green]Download complete: {dest_path}[/green]")
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Failed to download file: {e}[/red]")
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error during file download: {e}[/red]")
        raise

def is_valid_zip(file_path):
    """Check if a file is a valid ZIP archive."""
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            return True
    except zipfile.BadZipFile:
        return False
    except Exception as e:
        console.print(f"[red]Unexpected error while validating ZIP file: {e}[/red]")
        return False

def extract_zip(zip_path, extract_folder):
    try:
        console.print(f"[blue]Validating ZIP file: {zip_path}[/blue]")
        if not is_valid_zip(zip_path):
            raise zipfile.BadZipFile(f"The file {zip_path} is not a valid ZIP archive.")
        console.print(f"[blue]Extracting ZIP file {zip_path} to {extract_folder}...[/blue]")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file in track(zip_ref.namelist(), description="Extracting files", style="cyan"):
                zip_ref.extract(file, extract_folder)
        console.print(f"[green]Extraction complete! Files extracted to {extract_folder}[/green]")
    except zipfile.BadZipFile:
        console.print(f"[red]The file {zip_path} is not a valid ZIP file.[/red]")
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error during extraction: {e}[/red]")
        raise

def move_jar_files(source_folder, destination_folder):
    try:
        console.print(f"[blue]Searching for JAR files in {source_folder}...[/blue]")
        if not os.path.exists(source_folder):
            raise FileNotFoundError(f"Source folder does not exist: {source_folder}")
        jar_files = [file for file in os.listdir(source_folder) if file.endswith(".jar")]
        if not jar_files:
            console.print("[yellow]No JAR files found in the source folder.[/yellow]")
            return
        os.makedirs(destination_folder, exist_ok=True)
        for jar_file in track(jar_files, description="Moving JAR files", style="magenta"):
            shutil.move(os.path.join(source_folder, jar_file), destination_folder)
        console.print(f"[green]All JAR files moved to '{destination_folder}'[/green]")
    except Exception as e:
        console.print(f"[red]Unexpected error while moving JAR files: {e}[/red]")
        raise

def update_modpacks_json(modpacks_file, modpack_key, modpack_name, mod_loader, version):
    try:
        console.print("[blue]Updating 'modpacks.json'...[/blue]")
        modpacks_data = {"packs": {}}
        if modpacks_file.exists():
            with open(modpacks_file, "r", encoding="utf-8") as f:
                try:
                    modpacks_data = json.load(f)
                except json.JSONDecodeError:
                    console.print("[yellow]'modpacks.json' is corrupted. Overwriting it.[/yellow]")
        if modpack_key not in modpacks_data["packs"]:
            modpacks_data["packs"][modpack_key] = {
                "name": modpack_name,
                "version": version,
                "modLoader": mod_loader
            }
            console.print(f"[green]Added entry for '{modpack_name}'.[/green]")
        else:
            console.print(f"[yellow]Entry for '{modpack_name}' already exists.[/yellow]")
        with open(modpacks_file, "w", encoding="utf-8") as f:
            json.dump(modpacks_data, f, indent=4)
        console.print("[green]'modpacks.json' has been updated![/green]")
    except Exception as e:
        console.print(f"[red]Unexpected error while updating 'modpacks.json': {e}[/red]")
        raise

def main():
    modpack_zip_url = "https://next.buettner.tech/s/2e3Y7r6MTCeTCRL/download/mods.zip"
    addons_zip_url = "https://next.buettner.tech/s/pdXPP5TJepyw6SZ/download/addons.zip"
    
    base_path = Path.home() / "AppData/Roaming/.minecraft/labymod-neo"
    modpack_path = base_path / "modpacks/christmas2024/fabric/1.21.1/mods"
    addons_path = base_path / "modpacks/christmas2024/addons"
    modpacks_file = base_path / "modpacks/modpacks.json"
    
    modpack_key = "christmas2024"
    modpack_name = "Christmas 2024"
    mod_loader = "fabric"
    version = "1.21.1"
    
    if not base_path.exists():
        console.print("[red]Labymod does not seem to be installed. Aborting.[/red]")
        input("Press any key to exit...")
        return
    
    temp_dir = tempfile.mkdtemp()
    console.print(f"[cyan]Using temporary directory: {temp_dir}[/cyan]")
    try:
        modpack_zip_path = os.path.join(temp_dir, "modpack.zip")
        download_file(modpack_zip_url, modpack_zip_path)
        if not is_valid_zip(modpack_zip_path):
            raise zipfile.BadZipFile(f"The downloaded file {modpack_zip_path} is not a valid ZIP archive.")
        modpack_folder = os.path.join(temp_dir, "modpack")
        os.makedirs(modpack_folder, exist_ok=True)
        extract_zip(modpack_zip_path, modpack_folder)
        move_jar_files(modpack_folder, modpack_path)

        addons_zip_path = os.path.join(temp_dir, "addons.zip")
        download_file(addons_zip_url, addons_zip_path)
        if not is_valid_zip(addons_zip_path):
            raise zipfile.BadZipFile(f"The downloaded file {addons_zip_path} is not a valid ZIP archive.")
        addons_folder = os.path.join(temp_dir, "addons")
        os.makedirs(addons_folder, exist_ok=True)
        extract_zip(addons_zip_path, addons_folder)
        move_jar_files(addons_folder, addons_path)

        update_modpacks_json(modpacks_file, modpack_key, modpack_name, mod_loader, version)
        console.print("[bold green]Process completed successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            console.print(f"[cyan]Cleaned up temporary directory: {temp_dir}[/cyan]")

    input("Press any key to exit...")

if __name__ == "__main__":
    main()
