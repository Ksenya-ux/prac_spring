import os
import sys
import zlib

def get_git_directory(repo_path):
    git_dir = os.path.join(repo_path, '.git')
    return git_dir if os.path.isdir(git_dir) else None

def read_git_object(repo_path, object_hash):
    obj_path = os.path.join(repo_path, '.git', 'objects', object_hash[:2], object_hash[2:])
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

def get_branch_commit_hash(repo_path, branch_name):
    branch_path = os.path.join(repo_path, '.git', 'refs', 'heads', branch_name)
    if not os.path.isfile(branch_path):
        print(f"Branch '{branch_name}' not found", file=sys.stderr)
        return None
    
    with open(branch_path, 'r') as f:
        return f.read().strip()

def show_last_commit(repo_path, branch_name):
    commit_hash = get_branch_commit_hash(repo_path, branch_name)
    if not commit_hash:
        return None, None
    
    raw_data = read_git_object(repo_path, commit_hash)
    null_sep = raw_data.find(b'\x00')
    commit_content = raw_data[null_sep + 1:] if null_sep != -1 else raw_data
    commit_info = parse_commit(commit_content)
    
    print(f"tree {commit_info.get('tree', '')}")
    for parent in commit_info.get("parents", []):
        print(f"parent {parent}")
    print(f"author {commit_info.get('author', '')}")
    print(f"committer {commit_info.get('committer', '')}")
    print()
    print(commit_info.get("message", ""))
    
    return commit_info, commit_hash

def parse_tree(tree_content):
    entries = []
    pos = 0
    content_len = len(tree_content)
    
    while pos < content_len:
        space_idx = tree_content.index(b" ", pos)
        mode = tree_content[pos:space_idx].decode()
        pos = space_idx + 1
        
        null_idx = tree_content.index(b"\x00", pos)
        filename = tree_content[pos:null_idx].decode()
        pos = null_idx + 1
        
        sha = tree_content[pos:pos + 20].hex()
        pos += 20
        
        obj_type = "tree" if mode == "40000" else "blob"
        entries.append((obj_type, sha, filename))
    
    return entries
