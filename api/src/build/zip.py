import tempfile
from zipfile import ZipFile, is_zipfile
from pathlib import Path


def write_to_zipfile(content: bytes, output_path: Path) -> None:
    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file.write(content)

        if not is_zipfile(temp_file):
            raise ValueError("The uploaded file is not a valid zip file")

        output_path.write_bytes(content)


def write_extended_zipfile(existing_zipfile: Path, additional_paths: list[Path], output_path: Path) -> None:
    with ZipFile(existing_zipfile, 'r') as existing_zip:
        with ZipFile(output_path, 'w') as new_zip:
            for item in existing_zip.infolist():
                data = existing_zip.read(item.filename)
                new_zip.writestr(item, data)
            
            for path in additional_paths:
                if path.is_file():
                    new_zip.write(path, path.name)
                elif path.is_dir():
                    for file_path in path.rglob('*'):
                        if file_path.is_file():
                            # When adding a directory, only the contents are appended to the zip
                            # e.g. adding "build/" will not create paths beginning with "build/" in the zip
                            arcname = file_path.relative_to(path)
                            new_zip.write(file_path, arcname)
