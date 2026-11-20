
from pathlib import Path
from docx2pdf import convert

# Folder containing Word documents
input_folder = Path("data/raw")

# Folder to store converted PDFs
output_folder = Path("data/pdf")

output_folder.mkdir(parents=True, exist_ok=True)

# Find all .docx files, including subfolders
word_files = list(input_folder.rglob("*.docx"))

if not word_files:
    print("No Word documents found!")
else:
    print(f"Found {len(word_files)} Word documents.")

    for file in word_files:

        output_file = output_folder / f"{file.stem}.pdf"

        try:
            if output_file.exists():
                print(f"Already exists: {output_file.name}")
                continue

            convert(str(file), str(output_file))

            print(f"Converted: {file.name}")

        except Exception as e:
            print(f"Failed: {file.name} - {e}")

    print("\nConversion process completed!")
