# github-gender-studies
Tool for recognizing a gender of GitHub user, with a help of 3rd party services. Runs locally using data from a local MySQL instance of a GitHub Torrent copy. Genders are recognized from a combination of name/surname only.

### License

The MIT License (MIT)

Copyright (c) 2015 WikiTeams.pl

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

##### Disclaimer

This software is for research purposes only and cannot be used for commercial purposes.

### Project structure
#### directory "sources"

Holds recognition modules divided by the type of Gender-API.

Can be either gender-api.com or genderchecker.com

#### file GenderAnalyzer.py

Interactive script for executing with proper settings and choosing the gender api.
