import argparse
from logger import scream

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--silent", help="no output at all? [True/False]", action="store_true")
    parser.add_argument("-v", "--verbose", help="verbose messaging? [True/False]", action="store_true")
    args = parser.parse_args()
    if args.silent:
        scream.disable_all = True
    if args.verbose:
        scream.intelliTag_verbose = True
        scream.say("verbosity turned on")

    print "Please select gender analyzer: "
    print "[1] - gender-api.com"
    print "[2] - genderchecker.com"

    var = raw_input("[1/2]: ")

    if (str(var) == '1'):
        from sources.gender_api import github_gender_finder
        github_gender_finder.execute_check()
    elif (str(var) == '2'):
        from sources.gender_checker import github_gender_finder
        github_gender_finder.execute_check()
