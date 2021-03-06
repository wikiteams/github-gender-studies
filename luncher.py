import argparse
from logger import scream

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--silent", help="Disable all output? [True/False]", action="store_true")
    parser.add_argument("-v", "--verbose", help="Enable verbose messaging? [True/False]", action="store_true")
    parser.add_argument("-i", "--interactive", help="Use interactive mode? [True/False]", action="store_true")
    parser.add_argument("-limit", "--small_test_chunk", help="Limit records to 500? [True/False]", action="store_true")
    parser.add_argument("-d", "--default", help="Lunch with defaults? [True/False]", action="store_true")

    args = parser.parse_args()
    if args.silent:
        scream.disable_all = True
    if args.verbose:
        scream.intelliTag_verbose = True
        scream.say("verbosity turned on")

    if args.default:
        from sources.namsor import github_gender_finder
        github_gender_finder.execute_check(False, ("users", "yes"))
    elif args.interactive:
        print "Please select gender analyzer: "
        print "[1] - gender-api.com"
        print "[2] - genderchecker.com"
        print "[3] - NamSor Gender API"

        var = raw_input("[1-3]: ")

        if (str(var) == '1'):
            from sources.gender_api import github_gender_finder
            github_gender_finder.execute_check()
        elif (str(var) == '2'):
            from sources.gender_checker import github_gender_finder
            github_gender_finder.execute_check()
        elif (str(var) == '3'):
            from sources.namsor import github_gender_finder
            github_gender_finder.execute_check(True if args.small_test_chunk else False)
        else:
            print "Wrong value inserted. Please chooce a number between 1 and 3 (inclusive)"
    else:
        raise NotImplementedError  # "Lunch interactive mode instead"
