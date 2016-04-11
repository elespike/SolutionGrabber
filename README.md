#SolutionGrabber

SolutionGrabber is a CLI program written in Python 3 for Windows. It will read a supplied text file containing paths, one per line, to specific directories or files to be copied.

If the path points to a specific file, SolutionGrabber will copy that file to the output folder.

If the path points to a specific directory, SG will recursively copy the directory to the output folder.

If the path points to a Visual Studio solution or project file, SG will copy all referenced files.

####Please note:
Existing files will be overwritten.

Directory structure will be maintained whenever possible.

Lines in the supplied text file starting with '#' will be ignored.

Run "SG.exe -h" to obtain the complete help text.
