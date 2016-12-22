#SolutionGrabber

SolutionGrabber is a CLI program written in Python 3 for Windows. It will read a supplied text file containing paths, one per line, to specific directories or files to be copied.

If the path points to a specific file, SolutionGrabber will copy that file to the output folder.

If the path points to a specific directory, SG will recursively copy the directory to the output folder.

If the path points to a Visual Studio solution or project file, SG will copy all referenced files.

####Please note:
Existing files will be overwritten.

Directory structure will be maintained whenever possible.

Lines in the supplied text file starting with '#' will be ignored; lines starting with '!' will be excluded.
>Examples:
"# this is a comment" will be ignored entirely.
>
"! file.csproj" and all included source files will not be copied even if other .sln or .csproj files include file.csproj.
>
"! example\_dir" will be created empty even if other .sln or .csproj files include example\_dir or files within it. **Without a trailing slash, directories whose name starts with example\_dir will be excluded**.
>
"! example\_dir\" will be created empty even if other .sln or .csproj files include example\_dir or files within it. With a trailing slash, other directories whose name starts with example\_dir will still be included, since the slash delineates example\_dir.

Run "SG.exe -h" to obtain the complete help text.

