"""

htapt.py
By DKY

== Hazard Team Asset Pruning Tool ==

(Version 0.0.0a DEV)

This tool is an organizational tool that is meant to help clean up any 
extraneous files in a mod distribution. It does this by scanning a directory's 
contents, searching each file for direct references to other files, and then 
building a list of all files that have no references.

"""

import os
import sys
import time
from datetime import timedelta

__version__ = '0.0.0a DEV'

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(HERE, 'BMS')

# 4-byte magic number for *.mdl files.
MDL_MAGIC = 'IDST'


def memoized(f):
    """ Simple memoization decorator. """
    
    _memo = {}
    
    def wrapper(*args, **kwargs):
        try:
            return _memo[(args, str(kwargs))]
            
        except KeyError:
            result = f(*args, **kwargs)
            _memo[(args, str(kwargs))] = result
            return result
            
    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    
    return wrapper
    
    
def relpath_from_abspath(absPath):
    """ Converts an absolute path to a path relative to BASE_DIR. """
    
    assert absPath.startswith(BASE_DIR)
    
    # The slice removes the leading backslash.
    return absPath.split(BASE_DIR, 1)[-1][1:]
    
    
def abspath_from_relpath(relPath):
    """ Converts a path relative to BASE_DIR to an absolute path. """
    
    assert not relPath.startswith(BASE_DIR)
    
    return os.path.join(BASE_DIR, relPath)
    
    
def find_all_files(dir):
    """ Returns a set of all file paths in the given directory. """
    
    assert os.path.isdir(dir)
    
    files = set()
    
    for item in os.listdir(dir):
        if item == '.svn':
            continue
            
        itemPath = os.path.join(dir, item)
        
        if os.path.isdir(itemPath):
            files.update(find_all_files(itemPath))
        else:
            files.add(relpath_from_abspath(itemPath))
            
    return files
    
    
@memoized
def without_leading_dir(path):
    """ Removes the the leading directory in FRONT of the given path. """
    
    result = '\\'.join(
            path
                .replace('\\', '/')
                .split('/')[1:]
        )
    
    if result.startswith('\\'):
        result = result[1:]
        
    return result
    
    
def process_data(data):
    """ Pre-process the given data to make textual string searches easier. """
    
    return (
        data
            .lower()                # Force lowercase
            .replace('/', '\\')     # Force backslashes
    )
    
    
def is_mdl_data(data):
    """ Determines whether or not the given data is that of a *.mdl file. """
    return data.startswith(MDL_MAGIC)
    
    
def model_contains(data, needle):
    """ Returns whether or not the given model data 'haystack' references the 
    given file 'needle'.
    
    """
    
    assert is_mdl_data(data)
    
    needle = needle.lower()
    
    # Don't deal with anything other than model materials.
    if not needle.startswith('materials\\') or not needle.endswith('.vmt'):
        return False
        
    needle = without_leading_dir(needle)
    
    dataParts = [item.lower() for item in data.split('\x00') if item]
    
    # The material path is usually the last string.
    materialPath = dataParts[-1]
    
    for item in dataParts[:-1]:
        if needle == os.path.join(materialPath, item) + '.vmt':
            return True
            
    return False
    
    
def file_data_contains(data, needle):
    """ Looks for the given file 'needle' in the data 'haystack'. """
    
    needle = needle.lower()
    
    return (
        
        # Special processing is required to resolve model material/skin 
        # references.
        is_mdl_data(data) and model_contains(data, needle) or
        
        # Check for sound files, whose references don't usually include the 
        # 'sound' directory in the path.
        needle.startswith('sound\\') and
            without_leading_dir(needle) in data or
            
        # Ditto for material files in the 'materials' directory.
        needle.startswith('materials\\') and (
            
            # Need to account for the fact that '.vmt' is omitted quite often 
            # in most files.
            needle.endswith('.vmt') and
                without_leading_dir(needle).replace('.vmt', '') in data or
                
            # Ditto for omitting the '.vtf' extension.
            needle.endswith('.vtf') and
                without_leading_dir(needle).replace('.vtf', '') in data or
                
            False
            
        ) or
        
        # The normal case.
        needle in data or
        
        False
        
    )
    
    
def depends_on(path, otherPath):
    """ Returns whether or not the given path depends on the given otherPath.
    
    Mostly useful for resolving hidden dependencies, like for models.
    
    """
    
    if path == 'hc_changelog.txt':
        return otherPath in (
            'hc_changelog_chris.txt',
            'hc_changelog_dky.txt',
            'hc_changelog_jeff.txt',
        )
        
    elif path.endswith('.vmf'):
        mapName = os.path.basename(path).replace('.vmf', '')
        return otherPath in (
            'maps\\{}.bsp'.format(mapName),
            'maps\\graphs\\{}.ain'.format(mapName),
            'maps\\soundcache\\{}.cache'.format(mapName),
        )
        
    elif path.endswith('.mdl'):
        MODEL_EXTENSIONS = (
            '.dx80.vtx',
            '.dx90.vtx',
            '.phy',
            '.sw.vtx',
            '.vvd',
        )
        
        for ext in MODEL_EXTENSIONS:
            if otherPath == path.replace('.mdl', ext):
                return True
                
    return False
    
    
def should_pursue_references(path):
    """ Given a file path, returns whether or not we are interested in seeing 
    whether or not the file contains additional references to other files.
    
    """
    
    return not (
        path.endswith('.wav') or
        path.endswith('.bsp') or
        path.endswith('.vtf') or
        path.endswith('.cache') or
        'hc_changelog' in path
    )
    
    
def main():
    
    # Initialize the set of root files.
    # Someday, when I flesh this program out, I won't hard-code this.
    # But for now, this works for our purposes.
    ROOT_FILES = (
        '!readme.txt',
        'hc_changelog.txt',
        'hc_credits.txt',
        'maps\\!readme.txt',
        'maps\\src\\hc_fivenights.vmf',
        'maps\\src\\hc_t0a0.vmf',
        'maps\\src\\hc_t0a1.vmf',
        'maps\\src\\hc_t0a1a.vmf',
        'maps\\src\\hc_t0a2.vmf',
        'maps\\src\\hc_t0a2a.vmf',
        'maps\\src\\hc_t0a3.vmf',
        'resource\\closecaption_english.dat',
        'resource\\closecaption_english.txt',
        'particles\\particles_manifest.txt',
        'scripts\\character_manifest.txt',
        'scripts\\soundscapes_hazardcourse.txt',
        'scripts\\soundscapes_manifest.txt',
        'scripts\\talker\\response_rules.txt',
        'scripts\\talker\\t0a2_scenes.txt',
        'scripts\\talker\\t0a3_scenes.txt',
        'scripts\\titles.txt',
        'scenes\\scenes.image',
    )
    
    markedFiles = set(ROOT_FILES)
    unmarkedFiles = find_all_files(BASE_DIR) - markedFiles
    
    fileStack = list(ROOT_FILES)
    
    startTime = time.time()
    
    # Begin stack algorithm.
    while fileStack and unmarkedFiles:
        relPath = fileStack.pop()
        absPath = abspath_from_relpath(relPath)
        
        print "Scanning {}...".format(relPath)
        
        with open(absPath, 'rb') as f:
            data = f.read()
            
        # Process the data for faster text searching.
        data = process_data(data)
        
        # Check each item in the unmarked set to see if the file that we are 
        # currently analyzing depends on it.
        for unmarkedPath in set(unmarkedFiles):
            if (file_data_contains(data, unmarkedPath) or
                    depends_on(relPath, unmarkedPath)):
                    
                print "\tFound {}!".format(unmarkedPath)
                
                markedFiles.add(unmarkedPath)
                unmarkedFiles.remove(unmarkedPath)
                
                # Determine whether or not we should recursively find more 
                # references in the newly-found file.
                if should_pursue_references(unmarkedPath):
                    fileStack.append(unmarkedPath)
                    
    totalTime = timedelta(seconds=time.time() - startTime)
    
    # Convert the set to a list, so that we can sort it.
    unusedFiles = list(unmarkedFiles)
    unusedFiles.sort()
    
    # Write the list of unused files to an output file, so we can examine it.
    with open('sweep.txt', 'w') as f:
        f.write('\n'.join(unusedFiles))
        
    print "Found {} unused files.".format(len(unusedFiles))
    print "Time elapsed: {}".format(totalTime)
    print "Done!"
    
    return 0
    
    
if __name__ == '__main__':
    sys.exit(main())
    