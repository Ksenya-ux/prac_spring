import zlib,os, sys
from pathlib import Path

def get_git_dir(repo_path):
	git_dir = os.path.join(repo_path, '.git')
	return git_dir if os.path.isdir(git_dir) else None
