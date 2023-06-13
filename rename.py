from os import listdir, rename, getcwd, link, walk, mkdir
from os.path import isfile, isdir, join, basename
import re
import json
import argparse
import shutil

ONE_PIECE_DIR_NAME = "One Piece [tvdb4-81797]"

args = None

# set_ref_file_vars sets the episode and cover page reference files as global variables
# because they're often referenced in the script
def set_ref_file_vars(episodes_ref_file_path, coverpage_ref_file_path):
    global episodes_ref_file
    episodes_ref_file = episodes_ref_file_path
    global coverpage_ref_file
    coverpage_ref_file = coverpage_ref_file_path


# set_mapping sets mapping of One Pace episodes as global variables
# because they're often referenced in the script
def set_mapping(episode_mapping_value, coverpage_mapping_value):
    global episode_mapping
    episode_mapping = episode_mapping_value
    global coverpage_mapping
    coverpage_mapping = coverpage_mapping_value


# load_json_file takes a JSON file path
# and returns a JSON object of it.
def load_json_file(file):
    with open(file) as f:
        try:
            return json.load(f)
        except ValueError as e:
            print("Failed to load the file \"{}\": {}".format(file, e))
            exit

    return None


# list_mkv_files_in_directory returns all the files in the specified
# directory that have the .mkv extention
def list_mkv_files_in_directory(directory):
    ret_files = []
    for path, subdirs, files in walk(directory):
        for name in files:
            if "mkv" in name:
                ret_files.append(join(path, name))
    return ret_files
    #return [f for f in listdir(directory) if (isfile(join(directory, f)) and "mkv" in f)]


# generate_new_name_for_episode parses the original one pace file name
# and tries to match it with the reference episodes. 
# It returns the new name the file should have
def generate_new_name_for_episode(original_file_name):
    reg = re.search(r'\[One Pace\]\[.*\] (.*?) (\d\d?) \[(\d+p)\].*\.mkv', original_file_name)

    if (reg is not None):
        arc_name = reg.group(1)
        arc_ep_num = reg.group(2)
        resolution = reg.group(3)

        arc = episode_mapping.get(arc_name)
        if (arc is None):
            raise ValueError("\"{}\" Arc not found in file {}".format(arc_name, episodes_ref_file))

        episode_number = arc.get(arc_ep_num)
        if ((episode_number is None) or (episode_number == "")):
            raise ValueError("Episode {} not found in \"{}\" Arc in file {}".format(arc_ep_num, arc_name, episodes_ref_file))

        return [arc_name, "One.Piece.{}.{}.mkv".format(episode_number, resolution)]

    reg = re.search(r'\[One Pace\]\ Chapter\ (\d+-\d+) \[(\d+p)\].*\.mkv', original_file_name)

    if (reg is not None):
        arc_name = "Dressrosa"
        chapters = reg.group(1)
        resolution = reg.group(2)

        arc = episode_mapping.get(arc_name)
        if (arc is None):
            raise ValueError("\"{}\" Arc not found in file {}".format(arc_name, episodes_ref_file))

        episode_number = arc.get(chapters)
        if ((episode_number is None) or (episode_number == "")):
            raise ValueError("\"{}\" Episode not found in file {}".format(original_file_name, chapters_ref_file))

        return ["Dressrosa", "One.Piece.{}.{}.mkv".format(episode_number, resolution)]
    
    reg = re.search(r'\[One Pace\]\[.*\] (.*?) \[(\d+p)\].*\.mkv', original_file_name)

    if (reg is not None):
        episode_name = reg.group(1)
        resolution = reg.group(2)
        
        coverpage = coverpage_mapping.get(episode_name)
        
        arc_name = coverpage.get("Arc")
        arc_ep_num = coverpage.get("Episodes")
        
        arc = episode_mapping.get(arc_name)
        if (arc is None):
            raise ValueError("\"{}\" Arc not found in file {}".format(arc_name, episodes_ref_file))

        episode_number = arc.get(arc_ep_num)
        if ((episode_number is None) or (episode_number == "")):
            raise ValueError("Episode {} not found in \"{}\" Arc in file {}".format(arc_ep_num, arc_name, episodes_ref_file))


        return [arc_name, "One.Piece.{}.{}.mkv".format(episode_number, resolution)]

    raise ValueError("File \"{}\" didn't match the regexes".format(original_file_name))


def main():
    parser = argparse.ArgumentParser(description='Rename One Pace files to a format Plex understands')
    parser.add_argument("-af", "--arc-file", nargs='?', help="Path to the file containing the different arcs", default="arc-directories.json")
    parser.add_argument("-mf", "--map-file", nargs='?', help="Path to the file containing the tvdb4 mapping", default="tvdb4.mapping")
    parser.add_argument("-rf", "--reference-file", nargs='?', help="Path to the episodes reference file", default="episodes-reference.json")
    parser.add_argument("-crf", "--coverpage-reference-file", nargs='?', help="Path to the cover page reference file", default="coverpage-reference.json")
    parser.add_argument("-d", "--directory", nargs='?', help="Data directory (aka path where the mkv files are)", default=None)
    parser.add_argument("-t", "--target-dir", nargs='?', help="Target directory (aka path where the mkv files will be placed)", default=None)
    parser.add_argument("--hardlink", action="store_true", help="Hardlink files to new directory instead of moving")
    parser.add_argument("--dry-run", action="store_true", help="If this flag is passed, the output will only show how the files would be renamed")
    parser.add_argument("--clear", action="store_true", help="If this flag is passed, the target dir will be cleared and rebuilt from scratch")
    args = vars(parser.parse_args())
    
    if args["clear"]:
        if args["target_dir"] is None:
            sys.exit("--clear must be used in combination with --target-dir")
        
        target_basename = basename(args["target_dir"])
        if ONE_PIECE_DIR_NAME != target_basename:
            sys.exit("The directory \"{}\" to be clear is not a valid One Piece directory, should be named {}".format(args["target_dir"], ONE_PIECE_DIR_NAME))
        
        print("Removing: {}".format(args["target_dir"]))
        shutil.rmtree(args["target_dir"])
        mkdir(args["target_dir"])
        arc_list = load_json_file(args["arc_file"])
        for arc in arc_list:
            folder_dir = join(args["target_dir"], arc)
            print("Making: {}".format(folder_dir))
            mkdir(folder_dir)
            print("Copying: {} to {}".format(args["map_file"], join(folder_dir, basename(args["map_file"]))))
            shutil.copy(join(getcwd(), args["map_file"]), join(folder_dir, basename(args["map_file"])))

    set_ref_file_vars(args["reference_file"], args["coverpage_reference_file"])

    if args["directory"] is None:
        args["directory"] = getcwd()
    
    if args["target_dir"] is None:
        args["target_dir"] = getcwd()


    set_mapping(load_json_file(episodes_ref_file), load_json_file(coverpage_ref_file))

    video_files = list_mkv_files_in_directory(args["directory"])

    if len(video_files) == 0:
        print("No mkv files found in directory \"{}\"".format(args["directory"]))

    for file in video_files:
        try:
            new_episode_name = generate_new_name_for_episode(basename(file))
        except ValueError as e:
            print(e)
            continue

        full_path = None
        arc_name = "- " + new_episode_name[0]
        episode_name = new_episode_name[1]
        
        all_subdirs = [d for d in listdir(args["target_dir"]) if isdir(join(args["target_dir"], d))]
        count = len([i for i in all_subdirs if arc_name in i])

        if count > 1:
            raise ValueError("Found multiple matches for arc name \"{}\", in the directory \"{}\", subdirs \"{}\"".format(arc_name, args["target_dir"], all_subdirs))
        elif count == 0:
            raise ValueError("Unable to find directory for arc name \"{}\", in the directory \"{}\", subdirs \"{}\"".format(arc_name, args["target_dir"], all_subdirs))

        for subdir in all_subdirs:
            if arc_name in subdir:
                full_path = join(args["target_dir"], subdir, new_episode_name[1])
                break

        if (full_path is None) or (full_path == ""):
            raise ValueError("Unable to create full path for episode {} in arc {}".format(episode_name, new_episode_name[0]))

        if args["dry_run"]:
            print("DRYRUN: \"{}\" -> \"{}\"".format(file, full_path))
            continue
        
        if args["hardlink"]:
            link(file, full_path)
        else:
            rename(file, full_path)

if __name__ == "__main__":
    main()
