import zlib,os, sys
from pathlib import Path

def get_git_dir(repo_path):
	git_dir = os.path.join(repo_path, '.git')
	return git_dir if os.path.isdir(git_dir) else None
def read_git_obj(repo_path, obj_hash):
	obj_path = os.path.join(repo_path, '.git', 'objects', obj_hash[:2], obj_hash[2:])
    try:
        with open(obj_path, 'rb') as f:
            compressed_data = f.read()
        return zlib.decompress(compressed_data)
    except (FileNotFoundError, zlib.error):
        print(f"Git object {object_hash} not found or corrupted", file=sys.stderr)
        sys.exit(1)
