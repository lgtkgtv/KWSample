
import subprocess, os, re, sys
import time

script_name = 'kwgensow4git.py'

# Run "git log" to get (num_commits) last commits;
def get_owners_from_git_history(repo_root, since):
    cmd = ('git', 'log', '--since=' + since, '--name-status', '--pretty=format:%h >>>%ae<<<')
    print '===', cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo_root)
    out, err = p.communicate()
    if p.returncode != 0:
        print 'git return code:', p.returncode
        print 'stdout:', out
        print 'stderr:', err
        raise Exception('Failed to run git log')

    file_owners = dict()
    current_author = None
    for line in out.splitlines():
        #print '===', line
        m = re.match("[ACMRT]\t(.+)", line) # Added/Copied/Modified/Renamed/Type changed
        if m:
            path = m.group(1)
            path = path.replace('/', '\\')
            # only add author if file was not seen before; <= "git log" lists more recent commits first
            if current_author is not None:
                if not (path in file_owners):
                    file_owners[path] = current_author
            else:
                print 'Warning: unknown author of a file change:', line
            continue
        m = re.match("[DUXB]\t(.+)", line) # Deleted/Unmerged/X=unknown/Broken - ignore such file changes
        if m:
            continue
        m = re.search('>>>(.*)<<<', line) # author email -> username
        if m:
            current_author = m.group(1)
            continue
        if len(line.strip()) == 0:
            # commits are separated by empty strings
            current_author = None
            continue
        print 'Warning: unexpected "git log" line:', line
    return file_owners

# Get list of files under source control (used to filter out old files from .sow)
def list_git_files(repo_root):
    cmd = ('git', 'ls-files')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo_root)
    out, err = p.communicate()
    if p.returncode != 0:
        print 'git return code:', p.returncode
        print 'stdout:', out
        print 'stderr:', err
        raise Exception('Failed to run git ls-files')

    result = []
    for line in out.splitlines():
        l = line.strip()
        if len(l) > 0:
            path = l.replace('/', '\\')
            result.append(path)
    return result


def increment_stat(stats_dict, key):
    if key in stats_dict:
        stats_dict[key] = stats_dict[key] + 1
    else:
        stats_dict[key] = 1

# START HERE
def main():
    if len(sys.argv) != 3:
        print 'Usage: python ' + script_name +' <repository root dir> <target .sow file>'
        sys.exit(1) 
    repo_path = sys.argv[1] # 'D:\\build\\trunk\\CheckoutRoot\\REP'
    target_sow = sys.argv[2] # 'D:\\build\\trunk\\CheckoutRoot\\owners.sow'

    start_time = time.time()

    print 'Obtaining file owners data...'
    print '  repository path:', repo_path
    print '  target .sow file:', target_sow

    git_owners = get_owners_from_git_history(repo_path, '2013-01-01')
    print '  loaded', len(git_owners), 'file owners from recent git history'

    git_files = list_git_files(repo_path)
    print '  listed', len(git_files), 'files under version control (git ls-files)'
    print

    print 'Writing owners.sow file...'
    count_git = 0
    count_missing = 0
    scm_owner_stats = dict()
    applied_owner_stats = dict()
    with open(target_sow, 'w') as f:
        for path in git_files:
            # get scm owner first,
            if path in git_owners:
                owner = git_owners[path]
                count_git += 1
            else:
                count_missing +=1
                continue # do not write
            increment_stat(scm_owner_stats, owner)
            f.write(owner + ';' + path + '\n')

    print '  applied', count_git, ' owners from recent git history,', count_missing, 'file owners missing'
    print

    print 'SCM file owner statistics (owner - number of files):'
    for o in sorted(scm_owner_stats.keys()):
        print ' ', o, '-', scm_owner_stats[o]
    print
    print 'Applied file owner statistics - after mapping (owner - number of files):'
    for o in sorted(applied_owner_stats.keys()):
        print ' ', o, '-', applied_owner_stats[o]
    print

    print 'Done;', (time.time() - start_time), 'seconds'

if __name__ == "__main__" :
    main()
