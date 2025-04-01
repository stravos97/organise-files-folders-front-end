"""
Preset Configuration Manager for the File Organization System.

This module provides functions to generate predefined configuration dictionaries
for common organization tasks.
"""

import os
import yaml # Added yaml import

# Define possible paths at the module level for broader access (e.g., by tests)
possible_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "organize.yaml"), # Project config dir
    os.path.expanduser("~/.config/organize-tool/config.yaml"), # Linux/XDG config
    os.path.expanduser("~/Library/Application Support/organize-tool/config.yaml"), # macOS config
    os.path.join(os.getenv("APPDATA", ""), "organize-tool", "config.yaml") # Windows config
]

def get_find_duplicates_config():
    """Generate configuration for finding duplicate files."""
    return {
        'rules': [
            {
                'name': "Find Duplicate Files",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Documents")],  # Default location, user should change
                'subfolders': True,
                'filters': [
                    {'duplicate': {'detect_original_by': 'created'}}
                ],
                'actions': [
                    {'echo': "Found duplicate: {path} (Original: {duplicate.original})"},
                    # Default action is to move, user can modify
                    {'move': {'dest': os.path.expanduser("~/Duplicates/{relative_path}/"), 'on_conflict': 'rename_new'}}
                ]
            }
        ]
    }

def get_rename_photos_config():
    """Generate configuration for renaming photos using EXIF data."""
    return {
        'rules': [
            {
                'name': "Rename Photos with EXIF Data",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Pictures")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'arw', 'nef', 'cr2', 'dng']},
                    {'exif': True}
                ],
                'actions': [
                    {'echo': "Renaming photo: {path}"},
                    {'rename': "{exif.image.make}_{exif.image.model}_{exif.image.datetime.year}-{exif.image.datetime.month:02}-{exif.image.datetime.day:02}_{exif.image.datetime.hour:02}-{exif.image.datetime.minute:02}-{exif.image.datetime.second:02}.{extension}"}
                ]
            },
            {
                'name': "Rename Photos without EXIF Data (using creation date)",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Pictures")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'arw', 'nef', 'cr2', 'dng']},
                    {'not': {'exif': True}}, # Ensure EXIF filter is properly negated
                    {'created': True}
                ],
                'actions': [
                    {'echo': "Renaming photo without EXIF: {path}"},
                    # Using a simpler name format as fallback
                    {'rename': "{created.year}-{created.month:02}-{created.day:02}_{name}.{extension}"}
                ]
            }
        ]
    }

def get_photo_organization_config():
    """Generate configuration for organizing photos by date."""
    return {
        'rules': [
            {
                'name': "Organize Photos by Date (EXIF)",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Pictures/Unsorted")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'arw', 'nef', 'cr2', 'dng']},
                    {'exif': True}
                ],
                'actions': [
                    {'move': {'dest': os.path.expanduser("~/Pictures/Organized/{exif.image.datetime.year}/{exif.image.datetime.month:02}/"), 'on_conflict': 'rename_new'}}
                ]
            },
            {
                'name': "Organize Photos by Date (Created)",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Pictures/Unsorted")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'arw', 'nef', 'cr2', 'dng']},
                    {'not': {'exif': True}}, # Ensure EXIF filter is properly negated
                    {'created': True}
                ],
                'actions': [
                    {'move': {'dest': os.path.expanduser("~/Pictures/Organized/{created.year}/{created.month:02}/"), 'on_conflict': 'rename_new'}}
                ]
            }
        ]
    }

def get_music_organization_config():
    """Generate configuration for organizing music files."""
    # Note: organize-tool doesn't have built-in music tag filters.
    # This preset organizes by extension and finds duplicates.
    return {
        'rules': [
            {
                'name': "Organize Music Files by Extension",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Music/Unsorted")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['mp3', 'wav', 'aac', 'flac', 'm4a', 'wma', 'opus', 'ogg']}
                ],
                'actions': [
                    {'move': {'dest': os.path.expanduser("~/Music/Organized/{extension.upper()}/"), 'on_conflict': 'rename_new'}}
                ]
            },
            {
                'name': "Find Music Duplicates",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Music/Organized")], # Check organized folder
                'subfolders': True,
                'filters': [
                    {'extension': ['mp3', 'wav', 'aac', 'flac', 'm4a', 'wma', 'opus', 'ogg']},
                    {'duplicate': {'detect_original_by': 'created'}}
                ],
                'actions': [
                    {'echo': "Found music duplicate: {path} (Original: {duplicate.original})"},
                    {'move': {'dest': os.path.expanduser("~/Music/Duplicates/{relative_path}/"), 'on_conflict': 'rename_new'}}
                ]
            }
        ]
    }

def get_document_organization_config():
    """Generate configuration for organizing documents by type."""
    return {
        'rules': [
            {
                'name': "Organize Text Documents",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Documents/Unsorted")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['txt', 'rtf', 'md', 'tex']}
                ],
                'actions': [
                    {'move': {'dest': os.path.expanduser("~/Documents/Organized/Text/"), 'on_conflict': 'rename_new'}}
                ]
            },
            {
                'name': "Organize Office Documents",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Documents/Unsorted")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp']}
                ],
                'actions': [
                    {'move': {'dest': os.path.expanduser("~/Documents/Organized/Office/"), 'on_conflict': 'rename_new'}}
                ]
            },
            {
                'name': "Organize PDF Documents",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Documents/Unsorted")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['pdf']}
                ],
                'actions': [
                    {'move': {'dest': os.path.expanduser("~/Documents/Organized/PDF/"), 'on_conflict': 'rename_new'}}
                ]
            },
             {
                'name': "Organize Archive Files",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Documents/Unsorted")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']}
                ],
                'actions': [
                    {'move': {'dest': os.path.expanduser("~/Documents/Organized/Archives/"), 'on_conflict': 'rename_new'}}
                ]
            }
        ]
    }

def get_cleanup_rules_config():
    """Generate configuration for cleaning up temporary files and duplicates."""
    return {
        'rules': [
            {
                'name': "Clean Temporary Files",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Downloads")], # Default location
                'subfolders': True,
                'filters': [
                    {'extension': ['tmp', 'bak', 'cache', 'log', 'part', 'crdownload']}
                ],
                'actions': [
                    {'move': {'dest': os.path.expanduser("~/Cleanup/Temporary/"), 'on_conflict': 'rename_new'}}
                ]
            },
            {
                'name': "Find Duplicates in Downloads",
                'enabled': True,
                'targets': 'files',
                'locations': [os.path.expanduser("~/Downloads")], # Default location
                'subfolders': True,
                'filters': [
                    {'duplicate': {'detect_original_by': 'created'}}
                ],
                'actions': [
                    {'echo': "Found duplicate in Downloads: {path} (Original: {duplicate.original})"},
                    {'move': {'dest': os.path.expanduser("~/Cleanup/Duplicates/{relative_path}/"), 'on_conflict': 'rename_new'}}
                ]
            }
        ]
    }

def get_default_organization_config():
    """
    Generate a comprehensive default organization configuration.
    Tries to load from a standard location first.
    """
    # Try to find the default configuration file
    default_config_path = None
    # Use the module-level possible_paths list
    for path in possible_paths:
        if os.path.exists(path):
            default_config_path = path
            break

    if default_config_path:
        try:
            with open(default_config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load default config from {default_config_path}: {e}")
            # Fallback to a generated basic config if loading fails
            return { 'rules': [] } # Return empty rules if load fails
    else:
        # If no default file found, return an empty config
        print("Warning: Default organize.yaml not found in standard locations.")
        return { 'rules': [] }
