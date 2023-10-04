from sys import argv
from pathlib import Path
from hashlib import md5
from pprint import pprint

def walk(dir_path):
    """Iterates through a given directory and its subdirectories to list all files within.

    Args:
        dir_path (Path object): Path object of the parent directory.

    Returns:
        list: List containing the Path objects of every file in the parent directory and its subdirectories.
    """    
    file_list = list()
    for element in dir_path.iterdir():
        if element.is_symlink():
            continue
        if element.is_file():
            file_list.append(element)
        if element.is_dir():
            file_list.extend(walk(Path(element))) # Recursive search in subfolders
    return file_list

def calc_md5(file_path):
    """Computes the md5 hash of a given file.

    Args:
        file_path (string): String of the path to the file.

    Returns:
        string: md5 hash string of the given file.
    """
    hash = md5()
    with file_path.open("rb") as f:
        while chunk := f.read(8192):
            hash.update(chunk)
    return hash.hexdigest()

def get_file_hashes(file_paths_a, file_paths_b, roots):
    """Computes the md5 hashes of the files in the given lists.

    Args:
        file_paths_a (list(Path)): List of file Path objects of the older firmware filesystem.
        file_paths_b (list(Path)): List of file Path objects of the newer firmware filesystem.
        roots (list(Path)): List of the firmware filesystem roots.

    Returns:
        dict{str : [str/None, str/None]}: Dictionnary with the file names as keys and a list of their hashes as values.
    """
    dir_a_file_names = [str(file.relative_to(roots[0])) for file in file_paths_a]
    dir_b_file_names = [str(file.relative_to(roots[1])) for file in file_paths_b]
    file_names = set(dir_a_file_names) | set(dir_b_file_names)
    file_names = sorted(file_names)
    file_hashes = {file: [None,None] for file in file_names}
    # Possible improvement: multithread for loops
    for file in file_paths_a:
        checksum = calc_md5(file)
        file_hashes[str(file.relative_to(roots[0]))][0] = checksum

    for file in file_paths_b:
        checksum = calc_md5(file)
        file_hashes[str(file.relative_to(roots[1]))][1] = checksum
    return file_hashes

def differ(file_hashes_dict):
    """Checks a given file hash dictionnary for differences between hash a and hash b, then reports the changes.

    Args:
        file_hashes_dict (dict{str : [str/None, str/None]}): 
        Dictionnary with the file names as keys and a list of their hashes as values.
    """    
    changes = dict()
    for entry in file_hashes_dict:
        if file_hashes_dict[entry][0] is None:
            changes[entry] = {
                "Change type" : "Added",
                "First hash" : file_hashes_dict[entry][0],
                "Second hash" : file_hashes_dict[entry][1]
                }
        elif file_hashes_dict[entry][1] is None:
            changes[entry] = {
                "Change type" : "Removed",
                "First hash" : file_hashes_dict[entry][0],
                "Second hash" : file_hashes_dict[entry][1]
                }
        elif file_hashes_dict[entry][0] != file_hashes_dict[entry][1]:
            changes[entry] = {
                "Change type" : "Modified",
                "First hash" : file_hashes_dict[entry][0],
                "Second hash" : file_hashes_dict[entry][1]
                }
    pprint(changes)


def main():
    root_a = Path(argv[1])
    root_b = Path(argv[2])
    dir_a_files = walk(root_a)
    dir_b_files = walk(root_b)
    hash_dict = get_file_hashes(dir_a_files, dir_b_files, [root_a,root_b])
    differ(hash_dict)

if __name__=="__main__":
    if len(argv) != 3:
        print("USAGE: firmware_diff.py <Older firmware fs dir> <Newer firmware fs dir>")
    else:
        main()