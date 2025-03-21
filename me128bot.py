###########################################################################
# me128bot.py - ME 128 Discord bot
# Jason Loucks
#
# Checks the course Canvas for announcements and updates to specified
# folders and files. Only intended to work with one specific section of one
# specific course (ME 128-01, CSUS Spring 2025).
#
# TODO:
# - Clean up/reorganize for readability/efficiency
# - Add logging
#   - Only keep last 24 hrs
# - Add error handling?

###########################################################################
# imports
from canvasapi import Canvas  # docs: https://canvasapi.readthedocs.io/en/stable/index.html, live api: https://csus.instructure.com/doc/api/live
import discord                # docs: https://discordpy.readthedocs.io/en/stable/api.html
from discord.ext import tasks
import re                     # docs: https://docs.python.org/3/howto/regex.html

from canvas_bot import get_files_by_folder, get_new_updated, get_last_check
from config import CANVAS_URL, CANVAS_TOKEN, CANVAS_COURSE, CANVAS_FOLDERS, DISCORD_TOKEN, DISCORD_CHANNEL

###########################################################################
# functions

intents = discord.Intents.default()
client = discord.Client( intents = intents )

@tasks.loop( seconds = 30 )
async def run_checks( course, bot_channel ):
    # get time of last check and log current time
    this_check, last_check = get_last_check()

    # get current files, folders, and assignments
    all_assignments = list( course.get_assignments() )
    all_folders = list( course.get_folders() )
    folder_names = { folder.id: folder.name for folder in all_folders }
    all_files_by_folder = get_files_by_folder( course )

    # get new and updated ffa
    assignments = get_new_updated( all_assignments, last_check )
    files_by_folder = {}
    for folder in CANVAS_FOLDERS:
        files_by_folder[ folder ] = get_new_updated( all_files_by_folder[ folder ], last_check )

    if not ( assignments[ 'new' ] or any( files_by_folder[ folder ][ 'new' ] for folder in files_by_folder ) ):
        log_str = f'Check time: { this_check.astimezone() }\tResult: No files or assignments found!'
        print( log_str )
    else:
        message_str = '## New content posted!'
        if any( files_by_folder[ folder ][ 'new' ] for folder in files_by_folder ) or assignments[ 'new' ]: # if there are any new files or assignments
            for folder in CANVAS_FOLDERS: # doing it this way instead of `for folder in files_by_folder` to control the folder order
                if files_by_folder[ folder ][ 'new' ]: # if there are any new files in this folder
                    message_str += f'\n### { folder_names[ folder ] }'
                    for file in files_by_folder[ folder ][ 'new' ]:
                        file_url = 'https://csus.instructure.com/courses/' + str( CANVAS_COURSE ) + '/files/folder/' + folder_names[ folder ] + '?preview=' + str( file.id )
                        message_str += f'\n- [{ file.display_name }](<{ file_url.replace( ' ', '%20' ) }>)'
                        if ( 'hw' in file.display_name.lower() ) and ( 'solution' not in file.display_name.lower() ):
                            match = re.search( r'\d+', file.display_name)
                            if match:
                                digit = match.group()
                                assignment_name = 'Homework-' + digit
                                for assignment in all_assignments:
                                    if assignment_name in assignment.name:
                                        message_str += f' (Submission link: [{ assignment_name }](<{ assignment.html_url }>))'
                            else:
                                assignments_url = 'https://csus.instructure.com/courses/' + str( CANVAS_COURSE ) + 'assignments'
                                message_str += f' (Submission link: Couldn\'t find, should be posted soon or check [here](<{ assignments_url }))'
                elif folder == CANVAS_FOLDERS[ 2 ]: # if we are in the homework folder and there are no new HW files
                    if assignments[ 'new' ]: # if there is a new assignment
                        i = 0
                        for assignment in assignments[ 'new' ]:
                            if "homework" in assignment.name.lower():
                                if i == 0:
                                    message_str += f'\n### { folder_names[ folder ] }'
                                    i += 1
                                assignment_file_name = 'HW' + assignment.name.rsplit( '-', 1 )[ 1 ]
                                for file in all_files_by_folder[ folder ]:
                                    if ( assignment_file_name in file.display_name ) and ( 'solution' not in file.display_name.lower() ):
                                        file_url = 'https://csus.instructure.com/courses/' + str( CANVAS_COURSE ) + '/files/folder/' + folder_names[ folder ] + '?preview=' + str( file.id )
                                        message_str += f'\n- [{ file.display_name }](<{ file_url }>) (Submission link: [{ assignment.name }](<{ assignment.html_url }>))'
        await bot_channel.send( message_str )

        log_str = f'Check time: { this_check.astimezone() }\tResult: New files or assignments found!\t message_str: { repr( message_str ) }'
        print( log_str )

@client.event
async def on_ready():
    # init discord
    print( f'Successfully logged in to Discord' )
    bot_channel = client.get_channel( DISCORD_CHANNEL )

    # init canvas
    print( f'Logging in to Canvas...' )
    canvas = Canvas( CANVAS_URL, CANVAS_TOKEN )
    print( f'Successfully logged in to Canvas' )
    course = canvas.get_course( CANVAS_COURSE )

    run_checks.start( course, bot_channel )

@client.event
async def on_close():
    print(f'Successfully logged out')

###########################################################################
# main section

client.run( DISCORD_TOKEN )