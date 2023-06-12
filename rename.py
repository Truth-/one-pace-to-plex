from os import listdir, rename, getcwd, link
from os.path import isfile, join
import re
import json
import argparse

args = None

# set_ref_file_vars sets the chapterepisode reference files as global variables
# because they're often referenced in the script
def set_ref_file_vars(episodes_ref_file_path, chapters_ref_file_path):
    global episodes_ref_file
    episodes_ref_file = episodes_ref_file_path
    global chapters_ref_file
    chapters_ref_file = chapters_ref_file_path


# set_mapping sets mapping of One Pace episodes as global variables
# because they're often referenced in the script
def set_mapping(episode_mapping_value, chapter_mapping_value):
    global episode_mapping
    episode_mapping = episode_mapping_value
    global chapter_mapping
    chapter_mapping = chapter_mapping_value


# load_json_file takes a JSON file path
# and returns a JSON object of it.
def load_json_file(file):
    with open(file) as f:
        try:
            episode_mapping = json.load(f)
        except ValueError as e:
            print("Failed to load the file \"{}\": {}".format(file, e))
            exit

    return episode_mapping


# list_mkv_files_in_directory returns all the files in the specified
# directory that have the .mkv extention
def list_mkv_files_in_directory(directory):
    return [f for f in listdir(directory) if (isfile(join(directory, f)) and "mkv" in f)]


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
        chapters = reg.group(1)
        resolution = reg.group(2)

        episode_number = chapter_mapping.get(chapters)
        if ((episode_number is None) or (episode_number == "")):
            raise ValueError("\"{}\" Episode not found in file {}".format(chapters, chapters_ref_file))

        return ["Dressrosa", "One.Piece.{}.{}.mkv".format(episode_number, resolution)]

    raise ValueError("File \"{}\" didn't match the regexes".format(original_file_name))


def main():
    parser = argparse.ArgumentParser(description='Rename One Pace files to a format Plex understands')
    parser.add_argument("-rf", "--reference-file", nargs='?', help="Path to the episodes reference file", default="episodes-reference.json")
    parser.add_argument("-crf", "--chapter-reference-file", nargs='?', help="Path to the chapters reference file", default="chapters-reference.json")
    parser.add_argument("-d", "--directory", nargs='?', help="Data directory (aka path where the mkv files are)", default=None)
    parser.add_argument("-t", "--target-dir", nargs='?', help="Target directory (aka path where the mkv files will be placed)", default=None)
    parser.add_argument("--hardlink", action="store_true", help="Hardlink files to new directory instead of moving")
    parser.add_argument("--dry-run", action="store_true", help="If this flag is passed, the output will only show how the files would be renamed")
    args = vars(parser.parse_args())


    set_ref_file_vars(args["reference_file"], args["chapter_reference_file"] )

    if args["directory"] is None:
        args["directory"] = getcwd()
    
    if args["target_dir"] is None:
        args["target_dir"] = getcwd()


    set_mapping(load_json_file(episodes_ref_file), load_json_file(chapters_ref_file))

    video_files = list_mkv_files_in_directory(args["directory"])

    if len(video_files) == 0:
        print("No mkv files found in directory \"{}\"".format(args["directory"]))

    for file in video_files:
        try:
            new_episode_name = generate_new_name_for_episode(file)
        except ValueError as e:
            print(e)
            continue

        arc_name = new_episode_name[0]
        
        if args["directory"] != args["target_dir"]:
            all_subdirs = [d for d in os.listdir(args["target_dir"]) if os.path.isdir(d)]
            count = len([i for i in all_subdirs if i.contains(arc_name)])
            
            if count > 1:
                raise ValueError("Found multiple matches for arc name \"{}\", in the directory \"{}\", subdirs \"{}\"".format(arc_name, args["target_dir"], all_subdirs))
            elif count == 0:
                raise ValueError("Unable to find directory for arc name \"{}\", in the directory \"{}\", subdirs \"{}\"".format(arc_name, args["target_dir"], all_subdirs))

            for subdir in all_subdirs:
                if arc_name in subdir:
                    new_episode_name[1] = os.path.join(args["target_dir"], matched_dir, new_episode_name[1])
                    break


        if args["dry_run"]:
            print("DRYRUN: \"{}\" -> \"{}\"".format(file, new_episode_name[1]))
            continue
        
        if args["hardlink"]:
            link(file, new_episode_name[1])
        else:
            rename(file, new_episode_name[1])

if __name__ == "__main__":
    main()
