"""Create an ARM64/Python3.12 Lambda ZIP outside the source tree."""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='grinder-lambda-') as directory:
    target = Path(directory)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--platform', 'manylinux2014_aarch64',
                    '--implementation', 'cp', '--python-version', '3.12', '--only-binary=:all:',
                    '--target', str(target), '-r', str(root / 'requirements.txt')], check=True)
    shutil.copyfile(root / 'coach_handler.py', target / 'coach_handler.py')
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in target.rglob('*'):
            if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc':
                archive.write(file, file.relative_to(target))
print(args.output)
