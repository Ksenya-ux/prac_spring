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
        
def parse_commit(commit_data):
    parts = commit_data.decode("utf-8", errors="replace").split("\n\n", 1)
    header_lines = parts[0].splitlines()
    message = parts[1].strip() if len(parts) > 1 else ""
    
    commit_info = {"message": message, "parents": []}
    commit_info = {"message": message, "parents": []}
    for line in header_lines:
        key, _, value = line.partition(" ")
        if key == "tree":
            commit_info["tree"] = value
        elif key == "parent":
            commit_info["parents"].append(value)
        elif key == "author":
            commit_info["author"] = value
        elif key == "committer":
            commit_info["committer"] = value
            
    return commit_info
