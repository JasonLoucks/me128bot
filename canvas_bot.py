from canvasapi.assignment import Assignment
from canvasapi.file import File
from canvasapi.folder import Folder
from datetime import datetime, timezone
from pathlib import Path
import json
import os

from config import LAST_CHECK_DIR

def get_files_by_folder( course ):
    """
    Returns a dictionary of all files in a course, grouped by folder.
    
    Arguments:
        course (canvasapi.course.Course): Canvas course object.
    
    Returns:
        files_by_folder (dict): Dictionary with a key for each folder ID. Each key contains a list of Canvas file objects.
    """
    files = course.get_files()
    files_by_folder = {}
    for file in files:
        if file.folder_id not in files_by_folder:
            files_by_folder[ file.folder_id ] = []
        files_by_folder[ file.folder_id ].append( file )
    return files_by_folder

def get_new_updated( ffas, last_check ):
    """
    Gets new or updated files, folders, or assignments from Canvas since the last check.

    Arguments:
        ffas (list | canvasapi.paginated_list.PaginatedList): List of Canvas assignments, files, or folders.
        last_check (datetime): Timestamp of the last check (UTC).

    Returns:
        nu (dict): Dictionary with two keys:
            - "new" (list): List of FFAs created since the last check.
            - "updated" (list): List of FFAs updated since the last check.
    """
    nu = { "new":     [],
           "updated": [] }
    for ffa in ffas:
        if ffa:
            created_time = datetime.fromisoformat( ffa.created_at )
            updated_time = datetime.fromisoformat( ffa.updated_at )

            if created_time > last_check:
                nu[ "new" ].append( ffa )
            elif updated_time > last_check:
                nu[ "updated" ].append( ffa )
    return nu

def get_last_check():
    last_check_file = Path( LAST_CHECK_DIR + 'me128bot_last_check.log' )
    this_check = datetime.now(timezone.utc)

    # get time of last check and log current time
    if not last_check_file.exists() or os.stat( last_check_file ).st_size == 0:
        last_check = this_check
    else:
        with open( last_check_file, "r" ) as f:
            last_check = datetime.fromisoformat( f.read().strip() )
    
    with open( last_check_file, "w" ) as f:
        f.write( this_check.isoformat() )

    return this_check, last_check

def save_json( list, filename ):
    match list[ 0 ]:
        case Assignment():
            if not filename:
                filename = "assignments_curr.json"
            data = [ { "id":     a.id,
                       "due_at": a.due_at } for a in list ]
        case File():
            if not filename:
                filename = "files_curr.json"
            data = [ { "id":         a.id,
                       "updated_at": a.due_at } for a in list ]
        case Folder():
            if not filename:
                filename = "folders_curr.json"
            data = [ { "id":         a.id,
                       "updated_at": a.due_at } for a in list ]
    
    with open( filename, "w" ) as file:
        json.dump( data, file, indent = 4 )