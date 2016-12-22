import logging
import re
from argparse import ArgumentParser, RawTextHelpFormatter
from os       import access, W_OK, path, chmod, makedirs
from shutil   import copytree, rmtree, Error
from stat     import S_IWUSR
from sys      import stdout

try:
    # Python 3
    from urllib.parse import unquote
except ImportError:
    # Python 2
    from urllib import unquote


def grab_solution(sln_file, sln_lines, lang, parent_destination):
    parent_source = remove_invalid_chars(path.dirname(sln_file))
    logging.debug('parent_source is "{}".'.format(parent_source))
    for file_line in sln_lines:
        if 'Project' in file_line and 'proj"' in file_line:
            pattern = [r'= ".+", "(.+']
            if lang == CSH:
                # Ignore .vcxproj
                pattern.append('[^c|^x]')
            if lang == CPP:
                # Ignore .csproj
                pattern.append('[^s]')
            pattern.append('proj)"')

            unfiltered_search = re.search(pattern[0] + pattern[-1], file_line)
            search = re.search(''.join(pattern), file_line)
            if search is None:
                if unfiltered_search is None:
                    warn_parse_fail(file_line)
                continue

            source_proj_path      = parent_source      + search.group(1)
            destination_proj_path = parent_destination + search.group(1)
            source_proj_dir       = remove_invalid_chars(path.dirname(source_proj_path))
            destination_proj_dir  = remove_invalid_chars(path.dirname(destination_proj_path))
            logging.debug('source_proj_path is "{}".'     .format(source_proj_path))
            logging.debug('destination_proj_path is "{}".'.format(destination_proj_path))
            logging.debug('source_proj_dir is "{}".'      .format(source_proj_dir))
            logging.debug('destination_proj_dir is "{}".' .format(destination_proj_dir))

            if not path.isdir(destination_proj_dir):
                try:
                    makedirs(destination_proj_dir)
                    info_created_destination_path(destination_proj_dir)
                except IOError:
                    err_create_dir_fail(destination_proj_dir)

            if path.isfile(source_proj_path) and include_source(source_proj_path):
                try:
                    with open(source_proj_path, 'r') as a:
                        data = a.read()
                        a.seek(0)
                        grab_project(a.readlines(), source_proj_dir, destination_proj_dir)
                except IOError:
                    err_read_fail(source_proj_path)
                    continue
                try:
                    with open(destination_proj_path, 'w') as a:
                        a.write(data)
                    info_copied_file(source_proj_path, destination_proj_dir)
                except IOError:
                    err_write_fail(destination_proj_path)
            else:
                warn_filenotfound(source_proj_path)

def grab_project(proj_lines, sourcedir, parent_destination):
    for proj_line in proj_lines:
        if 'third-party-assemblies' in proj_line or '@' in proj_line:
            continue
        if 'Compile Include' in proj_line or 'EmbeddedResource Include' in proj_line:
            search = re.search(r'="(.+\.[0-9a-zA-Z]{1,10})"', proj_line)
            if search is None:
                warn_parse_fail(proj_line)
                continue

            resource = search.group(1)
            target_dir = remove_invalid_chars(parent_destination + path.dirname(resource))
            logging.debug('target_dir is "{}".'.format(target_dir))
            if '\\' in resource:
                if not path.isdir(target_dir):
                    try:
                        makedirs(target_dir)
                        info_created_destination_path(target_dir)
                    except IOError:
                        err_create_dir_fail(target_dir)

            source_file_path = unquote(path.join(sourcedir, resource))
            if path.isfile(source_file_path) and include_source(source_file_path):
                try:
                    with open(source_file_path, 'r') as a:
                        data = a.read()
                except IOError:
                    err_read_fail(source_file_path)
                    continue
                destination_file_path = parent_destination + resource
                try:
                    with open(destination_file_path, 'w') as a:
                        a.write(data)
                    info_copied_file(source_file_path, target_dir)
                except IOError:
                    err_write_fail(destination_file_path)
            else:
                warn_filenotfound(source_file_path)

def include_source(source_path):
    for source in excluded_sources:
        if source in source_path:
            return False
    return True

def info_created_destination_path(destination_path):
    logging.info('Created destination path "{}".'.format(destination_path))

def info_copied_file(filename, destination_path):
    logging.info('Copied\t"{}"\r\n\tinto\t"{}".'.format(filename, destination_path))

def warn_filenotfound(filepath):
    logging.warning('File excluded or not found, skipping "{}".'.format(filepath))

def warn_parse_fail(line):
    logging.warning('Unable to parse, skipping "{}".'.format(line))

def err_read_fail(filename):
    logging.exception('Unable to read, skipping "{}".'.format(filename))

def err_write_fail(filename):
    logging.exception('Unable to write, skipping "{}".'.format(filename))

def err_create_dir_fail(filename):
    logging.exception('Unable to create dir(s), skipping "{}".'.format(filename))

def remove_invalid_chars(_path):
    bad_set = ['<', '>', '"', '|', '?', '*']
    for char in bad_set:
        _path = _path.replace(char, '')
    if not _path.endswith('\\'):
        _path += '\\'
    return _path

# From http://stackoverflow.com/questions/2656322/python-shutil-rmtree-fails-on-windows-with-access-is-denied
def handle_readonly(function, pathname, exc_info):
    if not access(pathname, W_OK):
        # Is the error an access error ?
        chmod(pathname, S_IWUSR)
        function(pathname)
    else:
        raise


if __name__ == '__main__':
    ALL = 0
    CSH = 1
    CPP = 2

    parser = ArgumentParser(description='This program will read a supplied text file containing paths,'
                                        'one per line, to specific directories or files to be copied.\r\n'
                                        'If the path points to a specific file,\r\n\t'
                                        'SolutionGrabber will copy that file to the output folder.\r\n'
                                        'If the path points to a specific directory,\r\n\t'
                                        'SG will recursively copy the directory to the output folder.\r\n'
                                        'If the path points to a Visual Studio solution or project file,\r\n\t'
                                        'SG will copy all referenced files.\r\n\r\n'
                                        'Please note:\r\n'
                                        'Existing files will be overwritten.\r\n'
                                        'Directory structure will be maintained whenever possible.\r\n'
                                        "Lines in the supplied text file starting with '#' will be ignored.\r\n",
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('text_file', metavar='<Text file>', type=open,
                        help='Specifies a text file containing full paths'
                             'to the desired files or directories to be copied.\r\n'
                             'One path per line.')
    parser.add_argument('-o', '--out', default='C:\\SolutionGrabber', type=str,
                        help='Specifies the output directory. E.g., "Path" for "<working dir>\Path" or "D:\Path".\r\n'
                             'Default, "C:\\SolutionGrabber."')
    parser.add_argument('-p', '--purge', action='store_true', dest='purge',
                        help='Purges the output directory prior to copying any specified files,\r\n'
                             'recursively deleting all of its contents. Off by default.')
    parser.add_argument('-v', '--verbosity', default=2, type=int,
                        help='Specifies which levels of logging messages to show.\r\n'
                             '\t1: Errors only\r\n'
                             '\t2: Warnings and errors (default)\r\n'
                             '\t3: Informational messages plus the above\r\n'
                             '\t4: Debug messages plus the above')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--csh', action='store_const', const=CSH,
                       help='Given a project/solution file, copies only C# references.')
    group.add_argument('--cpp', action='store_const', const=CPP,
                       help='Given a project/solution file, copies only C++ references.')
    args = parser.parse_args()

    level_translator = {
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG}
    level = logging.WARNING
    if args.verbosity in level_translator:
        level = level_translator[args.verbosity]
    logging.basicConfig(format='\r\n%(asctime)s:%(msecs)03d %(levelname)s:\r\n\t%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        stream=stdout,
                        level=level)

    outdir = remove_invalid_chars(args.out)
    logging.debug('outdir is "{}".'.format(outdir))
    if path.isdir(outdir):
        if args.purge:
            try:
                rmtree(outdir, onerror=handle_readonly)
                logging.info('Purged directory "{}".'.format(outdir))
            except OSError:
                logging.exception('Error purging output directory "{}". Details below:'.format(outdir))
    if not path.isdir(outdir):
        try:
            makedirs(outdir)
            info_created_destination_path(outdir)
        except IOError:
            err_create_dir_fail(outdir)

    proj_type = ALL
    if args.csh:
        proj_type = args.csh
    if args.cpp:
        proj_type = args.cpp

    sources = [source.rstrip() for source in args.text_file.readlines()]
    global excluded_sources
    excluded_sources = []
    included_sources = []
    for source in sources:
        if source.startswith('#'):
            logging.info('Skipping "{}".'.format(source))
            continue
        elif source.startswith('!'):
            logging.info('Excluding "{}".'.format(source))
            excluded_sources.append(source.replace('!', '', 1).lstrip())
            continue
        else:
            logging.info('Including "{}".'.format(source))
            included_sources.append(source)

    for source in included_sources:
        logging.info('Attempting to grab "{}".'.format(source))
        if path.isfile(source):
            file_lines = []
            destination_path = ''
            fpath, fname = path.split(source)
            logging.debug('fpath is "{}".'.format(fpath))
            logging.debug('fname is "{}".'.format(fname))
            try:
                with open(source, 'r') as f:
                    file_data = f.read()
                    f.seek(0)
                    file_lines = f.readlines()
            except IOError:
                err_read_fail(source)
                continue
            destination_path = remove_invalid_chars(outdir + fpath.replace(':', ''))
            if not path.isdir(destination_path):
                try:
                    makedirs(destination_path)
                    info_created_destination_path(destination_path)
                except IOError:
                    err_create_dir_fail(destination_path)
            destination_name = destination_path + fname
            try:
                with open(destination_name, 'w') as f:
                    f.write(file_data)
                info_copied_file(source, destination_path)
            except IOError:
                err_write_fail(destination_name)
            if source.endswith('sln'):
                grab_solution(source, file_lines, proj_type, destination_path)
            elif source.endswith('proj'):
                grab_project(file_lines, remove_invalid_chars(path.dirname(source)), destination_path)
        elif path.isdir(source):
            try:
                copytree(source, outdir + source.replace(':', ''))
                logging.info('Recursively copied entire directory "{}" into output directory.'.format(source))
            except Error:
                logging.exception('Error copying directory "{}" into output directory. Details below:'.format(source))
                continue
        else:
            warn_filenotfound(source)
            continue

