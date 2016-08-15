#!/usr/bin/env python
import os


class Set_all:
    # default values for variables
    DEFAULT_HOME_DIR=os.path.expanduser("~")
    DEFAULT_MOUNT_DIR=os.path.abspath(os.path.dirname(__file__)) + "/to_mount"
    DEFAULT_NAME_FORMAT=".{}.old_v_crypt"
    DEFAULT_FILES_TO_CLEAN=['.cache', '.local/share/Trash']
    LOG_FILE = ".mounted"
    STATIC_MOUNTED = True
    STATIC_UNMOUNTED = False
    STATIC_VALL = True
    STATIC_VINFO = 3
    STATIC_VMEESSAGE = 2
    STATIC_VWARNING = 1
    STATIC_VERROR = 0
    STATIC_KEY_SYMLINK = 'delete'
    STATIC_KEY_CACHE = 'cache'

    @staticmethod
    def check(path_to_log):
        # checking if its mounted already
        # path_to_log is full path to log location
        # returns tuple with (Boolean, Dictionary)
        #   Boolean is True if its mounted already and False otherwise
        #   Dictionary contains files with description to rescure them
        #       delete - contain files that are only mounted
        #           contain only mounted files
        #           there were no files with that name while mounting, so were nothing to rename
        #       rename - files to delete, and rename to previus name
        #           contain files that were renamed
        #           files are renaming if makes problems with mounting files
        #               or just temp or cashe data, like .mozila or .bash_history or Trash
        if not os.path.exists(path_to_log) or not os.path.isfile(path_to_log):
            return Set_all.STATIC_UNMOUNTED, {}
        files_to_fix = {Set_all.STATIC_KEY_SYMLINK:[], Set_all.STATIC_KEY_CACHE:[]}
        action = files_to_fix.keys()[0]
        for line in open(path_to_log).readlines():
            line = line.strip()
            if line:
                if not line.startswith('/'):
                    files_to_fix[action].append(line)
                    continue
                for key in files_to_fix.keys():
                    if line.startswith('/{}'.format(key)):
                        action = key
                        break
        return Set_all.STATIC_MOUNTED, files_to_fix

    def __init__(self,
                 home_dir=DEFAULT_HOME_DIR,
                 mount_dir=DEFAULT_MOUNT_DIR,
                 files_to_mount = {},
                 name_format=DEFAULT_NAME_FORMAT,
                 files_to_clean=DEFAULT_FILES_TO_CLEAN,
                 verbose=STATIC_VMEESSAGE):
        # first if there should be logs
        self.verbose = verbose
        self.log("verbose set to {}".format(self.verbose), Set_all.STATIC_VINFO)

        # setting files/dirs locations
        self.mount_dir = mount_dir
        if not self.mount_dir.endswith("/"):
            self.mount_dir += "/"
        self.log("mount_dir set to {}".format(self.mount_dir), Set_all.STATIC_VINFO)
        self.home_dir = home_dir
        if not self.home_dir.endswith("/"):
            self.home_dir += "/"
        self.log("home_dir set to {}".format(self.home_dir), Set_all.STATIC_VINFO)
        self.files_to_mount = files_to_mount
        if not self.files_to_mount:
            self.files_to_mount = os.listdir(self.mount_dir)
        self.log("files_to_mount set to {}".format(self.files_to_mount), Set_all.STATIC_VINFO)
        self.log_file = self.LOG_FILE
        self.log("log_file set to {}".format(self.log_file), Set_all.STATIC_VINFO)

        # cache files to clen
        self.files_to_clean = []
        for file in files_to_clean:
            if file not in files_to_mount:
                self.files_to_clean.append(file)
        self.log("files_to_clean set to {}".format(self.files_to_clean), Set_all.STATIC_VINFO)

        # format used to changing names files i mount if there is conflict
        self.name_format = name_format
        self.log("name_format set to {}".format(self.name_format), Set_all.STATIC_VINFO)

        # checking if its mounted already
        self.log("Checking if is mounted already...", Set_all.STATIC_VINFO)
        self.mounted, self.files_to_fix = self.check(self.home_dir + self.log_file)
        self.log("mounted set to {}".format(self.name_format), Set_all.STATIC_VINFO)
        if self.files_to_fix:
            for key in self.files_to_fix:
                self.log("files_to_fix['{}'] set to {}".format(key, self.files_to_fix[key]), Set_all.STATIC_VINFO)
        else:
            self.log("files_to_fix set to {}".format(self.files_to_fix), Set_all.STATIC_VINFO, True)

    def log(self, message, prior=0, newline=False):
        # log message, if prior is bigger than verbose setting then no report
        #   its used in __init__ so no big change allowed
        # message - string to log
        # prior   - prioryty, bigger num is smaller prior
        #               prior = 0 is THE MOST IMPORTANT, while False is turned off
        # newline if set, adding addional new line at end
        if prior == 0 or self.verbose == True or (self.verbose != False and (self.verbose == True or self.verbose >= prior)):
            if prior == 0:
                prior = "ERROR!"
            elif prior == 1:
                prior = "Warning!"
            elif prior == 2:
                prior = "Message:"
            else:
                prior = "Info:"
            print prior, message
            if newline:
                print

    def action(self):
        # if not mounted yet then mount, otherwise unmount
        if self.mounted:
            return "Umounting", self.umount()
        return "Mounting", self.mount()

    def mount(self):
        # if not mounted yet then mount
        # return true if success
        if self.mounted == Set_all.STATIC_MOUNTED:
            return False

        self.files_to_fix[self.STATIC_KEY_SYMLINK] = []
        self.files_to_fix[self.STATIC_KEY_CACHE] = []
        self.log("File to mount..", Set_all.STATIC_VMEESSAGE)
        try:
            for file in self.files_to_mount:
                if self.rename(file):
                    self.log("Change name of {}".format(file), Set_all.STATIC_VMEESSAGE)
                if self.symlink(file):
                    self.log("Mounted {}".format(file), Set_all.STATIC_VMEESSAGE)
                    self.files_to_fix[self.STATIC_KEY_SYMLINK].append(file)
                else:
                    self.log("Cant mount file {}".format(file), Set_all.STATIC_VWARNING)
                    self.files_to_fix[self.STATIC_KEY_CACHE].append(file)
            self.log("Cache files...", Set_all.STATIC_VMEESSAGE)
            for file in self.files_to_clean:
                if self.rename(file):
                    self.log("Change name of {}".format(file), Set_all.STATIC_VMEESSAGE)
                    self.files_to_fix[self.STATIC_KEY_CACHE].append(file)
        except OSError as osError:
            self.log("Can not symlink all files, beacouse of an error.")
            self.log("Reversing changes..")
            self.fix_files()
            self.log(osError.message)
            return False

        with open(self.home_dir + self.log_file, 'w+') as log_file:
            for key in self.files_to_fix:
                if self.files_to_fix[key]:
                    log_file.write("/{}{}".format(key,os.linesep))
                    for value in self.files_to_fix[key]:
                        log_file.write(value)
                        log_file.write(os.linesep)
                        self.log("files_to_mount[{}] = {}".format(key, value), Set_all.STATIC_VINFO)

        self.mounted = Set_all.STATIC_MOUNTED
        return True

    def umount(self):
        # if mounted already then umount
        # return true if success
        if self.mounted == Set_all.STATIC_UNMOUNTED:
            return False

        if self.fix_files():
            # log_file shoud be destroyed in fix_files, but what if...
            #TODO: add checking if all files changed back correctly & removed
            if os.path.exists(self.home_dir + self.log_file):
                self.log("delete Log_file in location \"{}\"".format(self.log_file), Set_all.STATIC_VINFO)
                self.remove(self.log_file)
                if os.path.exists(self.log_file):
                    self.log("Log_file in location \"{}\", cant be deleted".format(self.log_file))
                else:
                    self.log("Deleted successfully.", Set_all.STATIC_VMEESSAGE)

            self.mounted = Set_all.STATIC_UNMOUNTED
            return True
        else:
            self.log("Cant Delete all files.")
            return False

    def fix_files(self, key=None):
        # fast way to fix all files, NOT USE FROM OUTSITE CLASS
        # removing & renameing changed files
        # key is either rename or delete, (or None, then is bouth at the same time)
        if not key:
            for key in self.files_to_fix:
                if not self.fix_files(key):
                    return False
            return True
        if key == self.STATIC_KEY_SYMLINK:
            symlink = True
        else:
            symlink = False
        self.log("Delete files with key \"{}\", thats: {}".format(key, self.files_to_fix[key]), self.STATIC_VMEESSAGE)
        files = list(self.files_to_fix[key])# coppy of list is nessesary
        for file in files:
            self.log("Delete file: {}".format(file), self.STATIC_VINFO)
            if self.remove(file, is_symlink=symlink):
                renamed_file = self.home_dir + self.changed_name(file)
                if not os.path.exists(renamed_file) or self.rename(file, reverse=True):
                    self.files_to_fix[key].remove(file)
                else:
                    self.log("Cant rename \"{}\"".format(renamed_file), self.STATIC_VINFO)
            else:
                self.log("Cant delete \"{}\"".format(file))
                return False
        return True

    def rename(self, file, new_name=None, reverse=False):
        # function with helping renaming files
        # changing name or restore previus name (if reverse is True)
        # file file name in home directory to change name
        # new_name if picked name, we can change that, if not use default function for that (remember to give full path to new_name)
        # reverse if False, then just change file to new_name, if True, then contrariwise
        # return true on success, false otherwise
        if not new_name:
            new_name = self.home_dir + self.changed_name(file)
        file = self.home_dir + file
        if reverse:
            temp = file
            file = new_name
            new_name = temp
        if os.path.exists(file):
            try:
                os.rename(file, new_name)
            except Exception as err:
                print "Error with rename({}, {})".format(file, new_name)
                print err.message
                return False
            return True
        return False

    def changed_name(self, file):
        # use chosed before self.name_format to change filename
        # file is file_name who is used to change, works with filenames NOT PATHs
        # return changed name
        return self.name_format.format(file)

    def remove(self, file, is_symlink=False):
        # remove file and linux temp file, who ends with ~
        # file is file name in home directory
        # is_symlink, remove only if this file is a symlink
        if file.endswith('/'):
            file = file.rstrip('/')
        file_full_path = self.home_dir + file
        temp_full_path = file_full_path + "~"

        # del linux temp file (ends with ~)
        if os.path.exists(temp_full_path):
            os.remove(temp_full_path)
            if os.path.exists(temp_full_path):
                self.log("Can not delete file {}".format(temp_full_path))

        if os.path.exists(file_full_path):
            # echeck if it should be symlink, then if its symlink
            if is_symlink and not os.path.islink(file_full_path):
                self.log("File \"{}\" is not symlink".format(file))
                return False
            # all ok, then remove
            os.remove(file_full_path)
            if os.path.exists(file_full_path):
                self.log("Can not delete file {}".format(file_full_path))
            else:
                return True
        else:
            self.log("There is no file to delete \"{}\"".format(file), self.STATIC_VMEESSAGE)
            return True
        return False

    def symlink(self, file):
        # if file exist in mount_dir then creaete symlink to home_dir
        # file is filename in home directory
        symlink_from = self.mount_dir + file
        symlink_to = self.home_dir + file

        if os.path.exists(symlink_from) and os.path.exists(os.path.dirname(symlink_to)):
            try:
                os.symlink(symlink_from, symlink_to)
                return True
            except IOError as ioError:
                # TODO: CHECK WHAT ERROR IS GIVING BY os.symlink
                self.log("Cant create symlink from \"{}\" to \"{}\"".format(symlink_from, symlink_to))
                self.log(ioError)
        else:
            self.log("Can not find file \"{}\" or location \"{}\" to create symlink".format(symlink_from,symlink_to), Set_all.STATIC_VWARNING)
        return False


#TODO: needeed variable: mouned, created, (changed_name, changed_to)
i = Set_all(verbose=Set_all.STATIC_VALL)
i.action()
#raw_input('Finish')
