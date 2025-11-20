import os
import shutil
from pathlib import Path

class FileManager:
    def __init__(self, base_dir="projects"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def create_project(self, metadata):
        """Creates the directory structure and config for a new brand project."""
        brand_name = metadata.get("brand_name")
        if not brand_name:
            raise ValueError("Brand name is required")
            
        brand_path = self.base_dir / brand_name
        brand_path.mkdir(exist_ok=True)
        (brand_path / "assets").mkdir(exist_ok=True)
        
        # Save Project Config
        import json
        (brand_path / "config.json").write_text(json.dumps(metadata, indent=4, ensure_ascii=False), encoding="utf-8")
        
        # Create default files
        tov_content = metadata.get("tov", "# Tone of Voice\n\nDefine your brand's voice here.")
        if not (brand_path / "tov.md").exists():
            (brand_path / "tov.md").write_text(tov_content, encoding="utf-8")
            
        if not (brand_path / "products.csv").exists():
            (brand_path / "products.csv").write_text("name,url,price,image_filename,keywords\n", encoding="utf-8")
        if not (brand_path / "semantic_core.csv").exists():
            (brand_path / "semantic_core.csv").write_text("keyword,volume,difficulty\n", encoding="utf-8")
        if not (brand_path / "pages.csv").exists():
            (brand_path / "pages.csv").write_text("url,title,h1\n", encoding="utf-8")
        if not (brand_path / "reference.html").exists():
            (brand_path / "reference.html").write_text("<!-- Paste your reference HTML here -->", encoding="utf-8")
            
        return str(brand_path)

    def list_projects(self):
        """Returns a list of existing project names."""
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]

    def get_project_path(self, brand_name):
        return self.base_dir / brand_name

    def read_file(self, brand_name, filename):
        path = self.base_dir / brand_name / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def get_tov(self, brand_name):
        """Retrieves the Tone of Voice content."""
        return self.read_file(brand_name, "tov.md")

    def save_file(self, brand_name, filename, content):
        path = self.base_dir / brand_name / filename
        path.write_text(content, encoding="utf-8")

    def save_asset(self, brand_name, uploaded_file):
        """Saves an uploaded file to the assets directory."""
        asset_path = self.base_dir / brand_name / "assets" / uploaded_file.name
        with open(asset_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(asset_path)

    def get_asset_names(self, brand_name):
        asset_dir = self.base_dir / brand_name / "assets"
        if asset_dir.exists():
            return [f.name for f in asset_dir.iterdir() if f.is_file()]
        return []
    
    def delete_project(self, brand_name):
        """Deletes a project folder and all its contents."""
        project_path = self.base_dir / brand_name
        if project_path.exists():
            shutil.rmtree(project_path)
            return True
        return False
