from os import listdir, rename, getcwd, walk
from os.path import isfile, join, abspath, basename, dirname, relpath, isdir
import re
import json
import argparse
import shutil

ONE_PIECE_DIR_NAME = "One Piece [tvdb4-81797]"

args = None

# set_ref_file_vars sets the episode, chapter, and cover page reference files as global variables
# because they're often referenced in the script
def set_ref_file_vars(episodes_ref_file_path, chapters_ref_file_path, coverpage_ref_file_path):
    global episodes_ref_file
    episodes_ref_file = episodes_ref_file_path
    global chapters_ref_file
    chapters_ref_file = chapters_ref_file_path
    global coverpage_ref_file
    coverpage_ref_file = coverpage_ref_file_path


# set_mapping sets mapping of One Pace episodes, chapters, and cover pages as global variables
# because they're often referenced in the script
def set_mapping(episode_mapping_value, chapter_mapping_value, coverpage_mapping_value):
    global episode_mapping
    episode_mapping = episode_mapping_value
    global chapter_mapping
    chapter_mapping = chapter_mapping_value
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

def get_files_from_directories(directory, recurse=False):
    video_files = list_mkv_files_in_directory(directory)
    if recurse: # check if subdirectories should be searched
        subdirs = [x[0] for x in walk(directory)] #recursively get all subdirectories
        #print(subdirs)
        for dir in subdirs[1:]: # loop through directories, skipping the first one (the root directory) as it's already done
            video_files += list_mkv_files_in_directory(dir)
    return video_files

# list_mkv_files_in_directory returns all the files in the specified
# directory that have the .mkv extention
def list_mkv_files_in_directory(directory):
    #get all filepaths for files in directory
    files = [f for f in listdir(directory) if (isfile(join(directory, f)) and "mkv" in f)]
    paths = []
    for f in files:
        paths.append(abspath(join(directory,f))) #get absolute path for each file
    return paths
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

        arc_ep_num = chapter_mapping.get(chapters)
        if (arc_ep_num is None):
            raise ValueError("\"{}\" Arc episode number not found in file {}".format(arc_ep_num, chapters_ref_file))

        arc = episode_mapping.get(arc_name)
        if (arc is None):
            raise ValueError("\"{}\" Arc not found in file {}".format(arc_name, episodes_ref_file))

        episode_number = arc.get(arc_ep_num)
        if ((episode_number is None) or (episode_number == "")):
            raise ValueError("Episode {} not found in \"{}\" Arc in file {}".format(arc_ep_num, arc_name, episodes_ref_file))

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
    parser.add_argument("-crf", "--chapter-reference-file", nargs='?', help="Path to the chapters reference file", default="chapters-reference.json")
    parser.add_argument("-cprf", "--coverpage-reference-file", nargs='?', help="Path to the cover page reference file", default="coverpage-reference.json")
    parser.add_argument("-d", "--directory", nargs='?', help="Data directory (aka path where the mkv files are)", default=None)
    parser.add_argument("-t", "--target-dir", nargs='?', help="Target directory (aka path where the mkv files will be placed)", default=None)
    parser.add_argument("-i", "--image-dir", nargs='?', help="Image directory (aka path where the season image files are located)", default="arc-images")
    parser.add_argument("--hardlink", action="store_true", help="Hardlink files to new directory instead of moving")
    parser.add_argument("--dry-run", action="store_true", help="If this flag is passed, the output will only show how the files would be renamed")
    parser.add_argument("-r", "--recurse", action="store_true", help="If this flag is passed, the script will search for mkv files in subdirectories as well")
    parser.add_argument("--clear", action="store_true", help="If this flag is passed, the target dir will be cleared and rebuilt from scratch")
    args = vars(parser.parse_args())
    
    if args["clear"]:
        if args["target_dir"] is None:
            sys.exit("--clear must be used in combination with --target-dir")
        
        target_basename = basename(args["target_dir"])
        if ONE_PIECE_DIR_NAME != target_basename:
            sys.exit("The directory \"{}\" to be clear is not a valid One Piece directory, should be named {}".format(args["target_dir"], ONE_PIECE_DIR_NAME))
        
        #print("Removing: {}".format(args["target_dir"]))
        shutil.rmtree(args["target_dir"])
        mkdir(args["target_dir"])
        arc_list = load_json_file(args["arc_file"])
        season_counter = 0
        for arc in arc_list:
            folder_dir = join(args["target_dir"], arc)
            #print("Making: {}".format(folder_dir))
            mkdir(folder_dir)
            #print("Copying: {} to {}".format(args["map_file"], join(folder_dir, basename(args["map_file"]))))
            target_file = join(folder_dir, basename(args["map_file"]))
            shutil.copy(join(getcwd(), args["map_file"]), target_file)
            chown(target_file, 568, 1000)

            if season_counter == 0:
                target_file = "Specials.PNG"
            else:
                target_file = f"Season{season_counter:02d}.PNG"

            target_fullpath = join(folder_dir, target_file)
            shutil.copy(join(getcwd(), args["image_dir"], target_file), target_fullpath)
            chown(target_fullpath, 568, 1000)
            season_counter += 1

    set_ref_file_vars(args["reference_file"], args["chapter_reference_file"], args["coverpage_reference_file"])

    if args["directory"] is None:
        args["directory"] = getcwd()
    
    if args["target_dir"] is None:
        args["target_dir"] = getcwd()


    set_mapping(load_json_file(episodes_ref_file), load_json_file(chapters_ref_file), load_json_file(coverpage_ref_file))

    video_files = get_files_from_directories(args["directory"], args["recurse"])

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

        #create some shorter file names for printing purposes        
        short_file = relpath(file,args["directory"])
        short_new_episode_path = relpath(subdir,args["directory"])

        if (full_path is None) or (full_path == ""):
            raise ValueError("Unable to create full path for episode {} in arc {}".format(episode_name, new_episode_name[0]))

        if args["dry_run"]:
            print("DRYRUN: \"{}\" -> \"{}\"".format(short_file, short_new_episode_path))
            continue
        
        if args["hardlink"]:
            print(f"Linking \"{short_file}\" to \"{short_new_episode_path}\"")
            link(file, full_path)
        else:
            print(f"Renaming \"{short_file}\" to \"{short_new_episode_path}\"")
            rename(file, full_path)

if __name__ == "__main__":
    main()
